from .models import ListeningTask, Question
from others.models import Results
import os
import json
from openai import OpenAI

def get_result(task_id, answers):
    try:
        task = ListeningTask.objects.get(id=task_id)
    except ListeningTask.DoesNotExist:
        return None

    questions = task.task_questions.all()
    correct_count = 0
    total_questions = questions.count()
    per_question_detail = []

    for question in questions:
        q_data = question.question or {}
        q_num = str(q_data.get('question_number', ''))
        correct_answer = question.answer
        user_answer = answers.get(q_num)
        
        is_correct = False
        if isinstance(correct_answer, dict):
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
            'correct_answer': correct_answer,
            'user_answer': user_answer,
            'is_correct': is_correct,
        })

    # IELTS Listening band score conversion (standard 40-question scale)
    def raw_to_band(raw, total):
        if total == 0: return 0.0
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

    overall_band = raw_to_band(correct_count, total_questions)
    accuracy_pct = (correct_count / total_questions * 100) if total_questions else 0

    # Build Gemini prompt for detailed feedback
    summary_lines = []
    for item in per_question_detail:
        status_str = "✓ Correct" if item['is_correct'] else "✗ Wrong"
        summary_lines.append(
            f"  Q{item['question_number']}: {status_str} "
            f"(correct: {item['correct_answer']}, given: {item['user_answer']})"
        )
    performance_summary = "\n".join(summary_lines)

    prompt = f"""
You are an expert IELTS Listening examiner. A student has just completed an IELTS Listening test.

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
  "score": {overall_band},
  "criteria": {{
    "Listening Accuracy": {overall_band},
    "Attention to Detail": {overall_band},
    "Vocabulary Range": {overall_band},
    "Spelling & Grammar": {overall_band}
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
  "performance_breakdown": "<2-3 sentence overall summary of the student's listening performance>"
}}
"""

    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        feedback = json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print("Gemini API error in listening get_result:", e)
        feedback = {
            "score": overall_band,
            "criteria": {
                "Listening Accuracy": overall_band,
                "Attention to Detail": overall_band,
                "Vocabulary Range": overall_band,
                "Spelling & Grammar": overall_band
            },
            "strengths": ["Completed the test"],
            "areas_for_improvement": ["Keep practicing"],
            "performance_breakdown": f"You scored {correct_count}/{total_questions}."
        }

    feedback["score"] = feedback.get("score", overall_band)
    feedback["raw_score"] = correct_count
    feedback["total"] = total_questions
    feedback["accuracy"] = round(accuracy_pct, 1)

    return feedback

def save_result(task_id, answers, user):
    try:
        task = ListeningTask.objects.get(id=task_id)
        
        title = Results.objects.filter(user=user, type='listening').count() + 1
        result = Results.objects.create(
            name=f"Results of Listening Test {title}",
            user=user,
            answers=answers,
            type='listening',
            score="0.0"
        )

        questions_list = []
        for question in task.task_questions.all():
            q_data = question.question or {}
            questions_list.append({
                'id': question.id,
                'question_number': q_data.get('question_number'),
                'question': q_data.get('text'),
                'type': question.type,
                'options': q_data.get('options'),
                'answer': question.answer
            })
        
        result.questions = questions_list
        result.save()
        
        return True, result
    except Exception as e:
        print("Error in listening save result: ", e)
        return False, str(e)
