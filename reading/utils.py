from .models import *
from django.db.models import Count


def get_reading_passage_queryset():
    # Fetch one random passage for each level to form a set
    p1 = ReadingPassage.objects.filter(level=1).order_by('?').first()
    p2 = ReadingPassage.objects.filter(level=2).order_by('?').first()
    p3 = ReadingPassage.objects.filter(level=3).order_by('?').first()

    # Get IDs of the passages that exist
    ids = [p.id for p in [p1, p2, p3] if p]
    
    # Return a queryset containing these passages
    queryset =  ReadingPassage.objects.filter(id__in=ids).prefetch_related('questions')

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
    return None



def save_result(set_id, answers, user):
    try:
        question_set = QuestionSet.objects.get(id=set_id)
    except QuestionSet.DoesNotExist:
        return None
    try:
        result = ReadingResult.objects.create(
            user=user,
            set=question_set,
            answers=answers
        )

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

    
