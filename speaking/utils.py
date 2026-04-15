import os
import json
import tempfile
import requests

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

def get_openrouter_response(prompt: str, model: str = "google/gemini-2.0-flash-001") -> str:
    """Helper to call OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
    if response.status_code != 200:
        raise Exception(f"OpenRouter API Error: {response.text}")
    
    return response.json()["choices"][0]["message"]["content"]



def generate_speaking_questions() -> dict:
    """
    Generates a complete set of IELTS Speaking test questions using Gemini AI.
    Nothing is saved to the database — a fresh set is generated each call.

    Returns a dict:
        {
            "part1": {
                "topic": str,
                "questions": [str, str, str, str, str]   # 5 questions
            },
            "part2": {
                "topic": str,
                "cue_card": str,          # multi-line instructions
                "points_to_cover": [str]  # bullet points
            },
            "part3": {
                "topic": str,
                "questions": [str, str, str, str, str]   # 4-5 discussion questions
            }
        }
    """
    prompt = """
    You are an official IELTS Speaking examiner creating a brand-new, unique test session.
    Generate a complete IELTS Speaking test with all 3 parts. Be creative and vary topics each time.

    Rules:
    - Part 1: YOU MUST NOT pick a single topic for Part 1. You MUST generate exactly 5 natural, conversational questions. EACH of the 5 questions MUST be about a COMPLETELY DIFFERENT and UNRELATED everyday topic. For example: Q1 about your hometown, Q2 about your favorite food, Q3 about your morning routine, Q4 about a recent holiday, and Q5 about learning languages. If any two questions are about the same topic, you have failed. Set the topic field to exactly "Random Assorted Topics".
    - Part 2: A cue card on a specific topic. It must have:
        * A clear topic title
        * A 1-sentence cue card description ("Describe a time when..." or "Describe a place/person/thing...")
        * Exactly 4 bullet points the candidate should cover (You should say...)
    - Part 3: 5 follow-up DISCUSSION questions related to the Part 2 topic — deeper, more abstract,
      opinion-based questions an examiner would ask after the cue card.

    Respond ONLY with a valid JSON object. No markdown, no extra text:
    {
      "part1": {
        "topic": "Random Assorted Topics",
        "questions": [
          "<q1 about topic A>",
          "<q2 about topic B (completely unrelated to A)>",
          "<q3 about topic C (completely unrelated to A and B)>",
          "<q4 about topic D (completely unrelated to others)>",
          "<q5 about topic E (completely unrelated to others)>"
        ]
      },
      "part2": {
        "topic": "<short topic label>",
        "cue_card": "<the cue card instruction sentence>",
        "points_to_cover": ["<point1>", "<point2>", "<point3>", "<point4>"]
      },
      "part3": {
        "topic": "<short topic label>",
        "questions": ["<q1>", "<q2>", "<q3>", "<q4>", "<q5>"]
      }
    }
    """

    raw = get_openrouter_response(prompt)
    # Strip markdown code fences if present
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)



def get_transcript(file) -> str:
    """
    Takes a Django InMemoryUploadedFile or TemporaryUploadedFile (audio),
    uploads it to Gemini Files API, generates a clean transcript, and
    returns the transcript as a plain string.
    """
    # Determine MIME type from file name
    name = getattr(file, 'name', 'audio.mp3')
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else 'mp3'
    mime_map = {
        'mp3':  'audio/mpeg',
        'mp4':  'audio/mp4',
        'wav':  'audio/wav',
        'ogg':  'audio/ogg',
        'webm': 'audio/webm',
        'flac': 'audio/flac',
        'm4a':  'audio/mp4',
        'aac':  'audio/aac',
    }
    mime_type = mime_map.get(ext, 'audio/mpeg')

    # Write the in-memory/temp file to a real temp file so Gemini can upload it
    suffix = f'.{ext}'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        # Upload audio to Gemini Files API
        uploaded_file = client.files.upload(
            file=tmp_path,
            config=types.UploadFileConfig(mime_type=mime_type),
        )

        # Generate transcript with a precise prompt
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                uploaded_file,
                (
                    "Please transcribe the spoken words in this audio file accurately and completely. "
                    "Output ONLY the verbatim transcript — no timestamps, no speaker labels, no comments, "
                    "no formatting annotations. Preserve punctuation naturally as spoken."
                ),
            ],
        )

        # Clean up remote file
        client.files.delete(name=uploaded_file.name)

        return response.text.strip()

    finally:
        # Always remove the local temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)





def get_result(part1_transcript: str, part2_transcript: str, part3_transcript: str,
               questions: dict) -> dict:
    """
    Evaluates IELTS Speaking transcripts for all 3 parts against the
    AI-generated questions (ephemeral — not from DB) using Gemini AI.

    Args:
        part1_transcript: Candidate's recorded response for Part 1 (all 5 qs combined)
        part2_transcript: Candidate's cue card response for Part 2
        part3_transcript: Candidate's discussion response for Part 3
        questions: The dict returned by generate_speaking_questions()

    Returns a dict with:
        - overall_band_score  (float, 0–9)
        - fluency             (float, 0–9)
        - pronunciation       (float, 0–9)
        - grammar             (float, 0–9)
        - vocabulary          (float, 0–9)
        - feedback            (str)
        - part_feedback       (dict with part1/part2/part3 individual feedback)
        - suggestions         (list[str])
    """
    p1 = questions.get('part1', {})
    p2 = questions.get('part2', {})
    p3 = questions.get('part3', {})

    p1_qs = '\n'.join(f'- {q}' for q in p1.get('questions', []))
    p2_cue = p2.get('cue_card', '')
    p2_pts = '\n'.join(f'- {pt}' for pt in p2.get('points_to_cover', []))
    p3_qs = '\n'.join(f'- {q}' for q in p3.get('questions', []))

    prompt = f"""
You are an official IELTS Speaking examiner. Evaluate the candidate's responses across all 3 parts.

=== PART 1 — Interview (Familiar Topics) ===
Questions asked:
{p1_qs}
Candidate's combined response:
{part1_transcript}

=== PART 2 — Long Turn (Cue Card) ===
Cue card: {p2_cue}
Points to cover:
{p2_pts}
Candidate's response:
{part2_transcript}

=== PART 3 — Two-way Discussion ===
Discussion questions:
{p3_qs}
Candidate's combined response:
{part3_transcript}

Evaluate strictly using the 4 official IELTS Speaking band descriptors:
1. Fluency & Coherence
2. Pronunciation
3. Grammatical Range & Accuracy
4. Lexical Resource (Vocabulary)

Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "overall_band_score": <float 0-9, multiples of 0.5>,
  "fluency": <float 0-9, multiples of 0.5>,
  "pronunciation": <float 0-9, multiples of 0.5>,
  "grammar": <float 0-9, multiples of 0.5>,
  "vocabulary": <float 0-9, multiples of 0.5>,
  "feedback": "<2-3 sentence holistic feedback>",
  "part_feedback": {{
    "part1": "<1-2 sentences on Part 1 performance>",
    "part2": "<1-2 sentences on Part 2 performance>",
    "part3": "<1-2 sentences on Part 3 performance>"
  }},
  "suggestions": [
    "<actionable suggestion 1>",
    "<actionable suggestion 2>",
    "<actionable suggestion 3>"
  ]
}}
"""

    raw = get_openrouter_response(prompt).strip()

    # Strip markdown code fences if Gemini wraps in ```json ... ```
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)