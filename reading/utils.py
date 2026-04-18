import random
from .models import *
from django.db.models import Count
import os
import json
from google import genai
from others.models import Results




def get_reading_passage_queryset():
    # Fetch random IDs for each level in an optimized way
    # This avoids expensive DB-side 'order_by(?)' operations
    passage_data = ReadingPassage.objects.filter(level__in=[1, 2, 3]).values_list('id', 'level')
    
    # Group IDs by level
    grouped_ids = {1: [], 2: [], 3: []}
    for pid, level in passage_data:
        if level in grouped_ids:
            grouped_ids[level].append(pid)
            
    # Select one random ID from each level
    ids = []
    for level in [1, 2, 3]:
        if grouped_ids[level]:
            ids.append(random.choice(grouped_ids[level]))
    
    # Return a queryset containing these passages
    queryset = ReadingPassage.objects.filter(id__in=ids).prefetch_related('questions')

    passage_ids = sorted(list(queryset.values_list('id', flat=True)))

    # Find if a set with these exact passages already exists
    # We match by ensuring the count of passages is the same AND each ID is present
    existing_sets = QuestionSet.objects.annotate(p_count=Count('passages')).filter(p_count=len(passage_ids))
    for p_id in passage_ids:
        existing_sets = existing_sets.filter(passages__id=p_id)
    
    question_set = existing_sets.first()

    if not question_set:
        # Create a new QuestionSet if not found
        question_set = QuestionSet.objects.create()
        question_set.passages.set(queryset)
        
        # Collect answers for the new set
        answers_map = {}
        for passage in queryset:
            for question in passage.questions.all():
                answers_map[str(question.question_number)] = question.answer
        
        question_set.answers = answers_map
        question_set.save()
    
    return question_set.id, queryset



def get_result(set_id, answers):

    try:
        question_set = QuestionSet.objects.get(id=set_id)
    except QuestionSet.DoesNotExist:
        return None

    correct_answers = question_set.answers or {}

    # ── 2. Normalise user answers to a dict {str(q_num): answer} ─────────────
    # Already normalised by the view — answers is a plain dict {"1": val, "2": val, ...}

    # ── 3. Score calculation ──────────────────────────────────────────────────
    correct_count  = 0
    total_questions = len(correct_answers)
    per_question_detail = []

    for q_num, correct_answer in correct_answers.items():
        user_answer = answers.get(str(q_num))
        is_correct  = False

        if isinstance(correct_answer, list):
            if isinstance(user_answer, list):
                is_correct = any(
                    str(ua).strip().lower() == str(ca).strip().lower()
                    for ua in user_answer for ca in correct_answer
                )
            else:
                is_correct = (
                    user_answer is not None and
                    str(user_answer).strip().lower() in [str(ca).strip().lower() for ca in correct_answer]
                )
        elif isinstance(correct_answer, dict):
            # Matching type: {left_key: right_value}
            if isinstance(user_answer, dict):
                is_correct = all(
                    str(user_answer.get(k, '')).strip().lower() == str(v).strip().lower()
                    for k, v in correct_answer.items()
                )
        else:
            is_correct = (
                user_answer is not None and
                str(user_answer).strip().lower() == str(correct_answer).strip().lower()
            )

        if is_correct:
            correct_count += 1

        per_question_detail.append({
            'question_number': q_num,
            'correct_answer' : correct_answer,
            'user_answer'    : user_answer,
            'is_correct'     : is_correct,
        })

    # IELTS Reading band score conversion (40-question scale approximation)
    raw_score = correct_count
    accuracy_pct = (correct_count / total_questions * 100) if total_questions else 0

    def raw_to_band(raw, total):
        if total == 0:
            return 0.0
        pct = raw / total
        if pct >= 0.97: return 9.0
        if pct >= 0.93: return 8.5
        if pct >= 0.87: return 8.0
        if pct >= 0.80: return 7.5
        if pct >= 0.73: return 7.0
        if pct >= 0.67: return 6.5
        if pct >= 0.60: return 6.0
        if pct >= 0.53: return 5.5
        if pct >= 0.47: return 5.0
        if pct >= 0.40: return 4.5
        if pct >= 0.33: return 4.0
        return 3.5

    overall_band = raw_to_band(raw_score, total_questions)

    # ── 4. Build Gemini prompt ────────────────────────────────────────────────
    summary_lines = []
    for item in per_question_detail:
        status_str = "✓ Correct" if item['is_correct'] else "✗ Wrong"
        summary_lines.append(
            f"  Q{item['question_number']}: {status_str} "
            f"(correct: {item['correct_answer']}, given: {item['user_answer']})"
        )
    performance_summary = "\n".join(summary_lines)

    prompt = f"""
You are an expert IELTS Reading examiner. A student has just completed an IELTS Reading test.

Test Statistics:
- Total Questions : {total_questions}
- Correct Answers : {correct_count}
- Accuracy        : {accuracy_pct:.1f}%
- Estimated Band  : {overall_band}

Per-question breakdown:
{performance_summary}

Based on the above data, generate a structured JSON feedback report. 
Return ONLY valid JSON with this exact structure (no markdown, no explanation):

{{
  "score": <overall_band_score as float, e.g. 7.5>,
  "criteria": {{
    "Reading Accuracy"    : <band 1-9 as float>,
    "Skimming & Scanning": <band 1-9 as float>,
    "Vocabulary Range"   : <band 1-9 as float>,
    "Time Management"    : <band 1-9 as float>
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
  "performance_breakdown": "<2-3 sentence overall summary of the student's reading performance>"
}}
"""

    # ── 5. Call Gemini API ────────────────────────────────────────────────────
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        client   = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
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
        print("Gemini API error in reading get_result:", e)
        # Graceful fallback – return rule-based result so the endpoint doesn't break
        feedback = {
            "score"   : overall_band,
            "criteria": {
                "Reading Accuracy"    : overall_band,
                "Skimming & Scanning" : round(overall_band - 0.5, 1),
                "Vocabulary Range"    : round(overall_band - 0.5, 1),
                "Time Management"     : round(overall_band, 1),
            },
            "strengths": [
                "Completed the test",
                f"Answered {correct_count} out of {total_questions} questions correctly",
            ],
            "areas_for_improvement": [
                "Review incorrect answers carefully",
                "Practice skimming for main ideas",
                "Build academic vocabulary",
            ],
            "performance_breakdown": (
                f"You scored {correct_count}/{total_questions} ({accuracy_pct:.1f}%), "
                f"which corresponds to an IELTS band of approximately {overall_band}. "
                "Keep practising to improve your reading speed and accuracy."
            ),
        }

    # Always attach raw score for the view to save
    feedback["score"]      = feedback.get("score", overall_band)
    feedback["raw_score"]  = raw_score
    feedback["total"]      = total_questions
    feedback["accuracy"]   = round(accuracy_pct, 1)

    return feedback



def save_result(set_id, answers, user):
    try:
        question_set = QuestionSet.objects.get(id=set_id)
    except QuestionSet.DoesNotExist:
        return None
    try:
        title = Results.objects.filter(user=user, type='reading').count() + 1
        result = Results.objects.create(
            name = f"Result of Reading Test {title}",
            user=user,
            answers=answers,
            type = 'reading',
            score = 0
        )

        passages_list = []
        for passage in question_set.passages.prefetch_related('questions'):
            p_data = {
                'id': passage.id,
                'title': passage.title,
                'content': passage.content,
                'level': passage.level,
                'questions': list(passage.questions.values('id', 'question_number', 'question', 'question_type', 'options'))
            }
            passages_list.append(p_data)
        
        result.questions = passages_list
        result.save()

        correct_count = 0
        total_questions = 0

        for question_number, correct_answer in question_set.answers.items():
            total_questions += 1
            user_answer = answers.get(question_number)

            if isinstance(correct_answer, list):
                if isinstance(user_answer, list):
                    if any(ans.lower() == correct.lower() for ans in user_answer for correct in correct_answer):
                        correct_count += 1
                else:
                    if user_answer and user_answer.lower() in [ans.lower() for ans in correct_answer]:
                        correct_count += 1
            else:
                if user_answer and str(user_answer).lower() == str(correct_answer).lower():
                    correct_count += 1

        result.score = correct_count
        result.save()

        return True, result

    except Exception as e:
        
        print("Error in reading save result: ", e)
        
        return False, None

    
