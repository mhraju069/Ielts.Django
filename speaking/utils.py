import os
import json
import base64
from openai import OpenAI

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

def get_openrouter_response(prompt: str, model: str = "google/gemini-2.0-flash-001") -> str:
    """Helper to call OpenRouter API using OpenAI client"""
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content



def generate_speaking_questions() -> dict:

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
    Converts audio file to base64 and gets transcript via OpenRouter.
    """
    name = getattr(file, 'name', 'audio.mp3')
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else 'mp3'
    
    # Read file and encode to base64
    audio_data = file.read()
    base64_audio = base64.b64encode(audio_data).decode('utf-8')
    
    mime_type = f"audio/{ext}"
    if ext == 'mp3': mime_type = "audio/mpeg"

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": (
                                "Please transcribe the spoken words in this audio file accurately and completely. "
                                "Output ONLY the verbatim transcript — no timestamps, no speaker labels, no comments. "
                                "Preserve punctuation naturally as spoken."
                            )
                        },
                        {
                            "type": "image_url", # OpenRouter uses image_url for multimodal content
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_audio}"
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Transcription error: {e}")
        return "Could not generate transcript."





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