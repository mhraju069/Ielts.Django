from .models import *
import os
import json
import mimetypes
from google import genai
from google.genai import types


def _load_image_part(image_field):
    """
    Reads an ImageField file from disk and returns a Gemini Part object.
    Returns None if the image cannot be read.
    """
    try:
        image_path = image_field.path
        mime_type, _ = mimetypes.guess_type(image_path)
        mime_type = mime_type or "image/jpeg"
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        return types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
    except Exception as e:
        print(f"Could not load graph image: {e}")
        return None


def get_result(answers, task_ids):
    """
    Evaluate user's writing answers using Gemini AI.

    For 'graph' type tasks that have an image attached, the graph image is
    sent alongside the student's answer so Gemini can visually evaluate how
    well the graph was described (multimodal).

    For 'text' (essay) tasks, only the written answer and task prompt are sent.

    Args:
        answers  (list | dict): Student's written responses.
        task_ids (list | int) : WritingTask PK(s) answered.

    Returns:
        dict: Structured IELTS feedback + db_responses for saving.
    """

    # ── 1. Normalise task_ids ─────────────────────────────────────────────────
    if not isinstance(task_ids, list):
        task_ids = [task_ids]

    # ── 2. Fetch task objects ordered by level ────────────────────────────────
    tasks = list(WritingTask.objects.filter(id__in=task_ids).order_by('level'))

    # ── 3. Normalise answers → list of strings ────────────────────────────────
    if isinstance(answers, dict):
        answers_list = [answers[k] for k in sorted(answers.keys(), key=lambda x: int(x))]
    elif isinstance(answers, list):
        answers_list = answers
    else:
        answers_list = [str(answers)]

    # ── 4. Build per-task data ────────────────────────────────────────────────
    task_sections  = []   # text blocks for the prompt
    image_parts    = []   # Gemini image Part objects (graph tasks only)
    answers_for_db = {}   # stored in WritingResult.responses

    for i, task in enumerate(tasks):
        user_answer = answers_list[i] if i < len(answers_list) else ""

        answers_for_db[str(task.id)] = {
            "task_title"   : task.title,
            "task_type"    : task.type,
            "task_level"   : task.level,
            "task_question": task.question,
            "user_answer"  : user_answer,
            "has_image"    : bool(task.type == "graph" and task.image),
        }

        # Graph task with image → load image for multimodal call
        if task.type == "graph" and task.image:
            part = _load_image_part(task.image)
            if part:
                image_parts.append((i + 1, part))   # (task_number, Part)
                task_sections.append(
                    f"--- TASK {i + 1} (Level {task.level} | Type: Graph/Chart) ---\n"
                    f"Task Question: {task.question}\n\n"
                    f"[Note: The graph image for Task {i + 1} has been provided above. "
                    f"Evaluate whether the student's description accurately reflects it.]\n\n"
                    f"Student Answer:\n{user_answer}\n"
                )
            else:
                # Image load failed → fall back to text-only for this task
                task_sections.append(
                    f"--- TASK {i + 1} (Level {task.level} | Type: Graph/Chart) ---\n"
                    f"Task Question: {task.question}\n\n"
                    f"Student Answer:\n{user_answer}\n"
                )
        else:
            # Essay / text task → text only
            task_sections.append(
                f"--- TASK {i + 1} (Level {task.level} | Type: Essay) ---\n"
                f"Task Question: {task.question}\n\n"
                f"Student Answer:\n{user_answer}\n"
            )

    combined_tasks = "\n\n".join(task_sections)

    # ── 5. Build prompt text ──────────────────────────────────────────────────
    graph_note = (
        "\nIMPORTANT: For graph/chart tasks, you have been provided the actual graph image. "
        "Use it to verify whether the student accurately identified key trends, data points, "
        "and comparisons. Penalise factual inaccuracies about the graph.\n"
        if image_parts else ""
    )

    prompt_text = f"""You are an expert IELTS Writing examiner.
{graph_note}
A student has submitted the following IELTS Writing test responses:

{combined_tasks}

Evaluate the student's responses based on official IELTS Writing band descriptors and return a structured JSON feedback report.
Return ONLY valid JSON with this exact structure (no markdown, no explanation outside the JSON):

{{
  "score": <overall band score as float, e.g. 7.0>,
  "criteria": {{
    "Task Achievement"      : <band 1-9 as float>,
    "Coherence & Cohesion"  : <band 1-9 as float>,
    "Lexical Resource"      : <band 1-9 as float>,
    "Grammar & Accuracy"    : <band 1-9 as float>
  }},
  "strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "areas_for_improvement": [
    "<area 1>",
    "<area 2>",
    "<area 3>"
  ],
  "answers": [
    {{
      "task"    : <task level as int, e.g. 1>,
      "type"    : "<graph or text>",
      "band"    : <individual task band score as float>,
      "feedback": "<2-3 sentence specific feedback for this task>"
    }}
  ],
  "performance_breakdown": "<2-3 sentence overall summary of the student's writing performance>"
}}
"""

    # ── 6. Build Gemini contents list (multimodal if graph images exist) ──────
    #
    # Layout: [image_1, label_1, image_2, label_2, ..., full_prompt_text]
    # Gemini reads the content in order, so images come before the text that
    # references them.
    contents = []
    for task_num, img_part in image_parts:
        contents.append(img_part)
        contents.append(
            types.Part.from_text(text=f"[Graph image for Task {task_num}]")
        )
    contents.append(types.Part.from_text(text=prompt_text))

    # ── 7. Call Gemini API ────────────────────────────────────────────────────
    try:
        api_key  = os.getenv("GEMINI_API_KEY")
        client   = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
        )
        raw_text = response.text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        feedback = json.loads(raw_text)

    except Exception as e:
        print("Gemini API error in writing get_result:", e)
        fallback_band = 5.0
        feedback = {
            "score"   : fallback_band,
            "criteria": {
                "Task Achievement"    : fallback_band,
                "Coherence & Cohesion": fallback_band,
                "Lexical Resource"    : fallback_band,
                "Grammar & Accuracy"  : fallback_band,
            },
            "strengths": [
                "Attempted all tasks",
                "Maintained a recognisable structure",
            ],
            "areas_for_improvement": [
                "Develop task-specific vocabulary",
                "Improve coherence between paragraphs",
                "Review grammar and sentence variety",
            ],
            "answers": [
                {
                    "task"    : task.level,
                    "type"    : task.type,
                    "band"    : fallback_band,
                    "feedback": "AI evaluation is currently unavailable. Please try again later.",
                }
                for task in tasks
            ],
            "performance_breakdown": (
                "AI evaluation could not be completed at this time. "
                "Your responses have been saved successfully."
            ),
        }

    # Attach DB payload — not exposed to the API response consumer
    feedback["db_responses"] = answers_for_db

    return feedback
