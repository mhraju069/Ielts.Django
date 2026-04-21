from rest_framework import generics, views, status
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import *
from .utils import generate_speaking_questions, get_transcript, get_result
from django.db import transaction
from others.models import Results, Task
from rest_framework.permissions import IsAuthenticated



class GenerateSpeakingSessionView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            task = Task.objects.get(user=request.user, module='speaking', completed=False)
            session = QuestionSet.objects.get(id=task.question)
            time = (session.start + session.duration) - timezone.now()
            total_seconds = int(time.total_seconds())
            if total_seconds <= 0:
                duration_str = "00:00:00"
            else:
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            return Response({
                'status': True,
                'session_id': str(session.id),
                **session.questions,
                'duration': duration_str,
            })
        except Task.DoesNotExist:
            try:
                questions = generate_speaking_questions()

                session = QuestionSet.objects.create(questions=questions)
                
                Task.objects.create(user=request.user, module='speaking', question=session.id, completed=False)

                return Response({
                    'status': True,
                    'session_id': str(session.id),
                    **questions,
                    'duration': "00:14:00",  # default speaking time
                })
            except Exception as e:
                return Response(
                    {'status': False, 'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
    # def get_remaining_time(self, request):
    #     try:
    #         task = Task.objects.get(user=request.user, module='speaking', completed=False)
    #         session = QuestionSet.objects.get(id=task.question)
    #         return Response({
    #             'status': True,
    #             'remaining_time': 14,
    #         })
    #     except Task.DoesNotExist:
    #         return Response(
    #             {'status': False, 'error': 'Speaking test session not found'},
    #             status=status.HTTP_404_NOT_FOUND,
    #         )




class SpeakingResultView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        part1_audio = data.get('audio1')
        part2_audio = data.get('audio2')
        part3_audio = data.get('audio3')
        session_id  = data.get('session')

        # Validation
        missing = [
            k for k, v in {
                'part1_audio': part1_audio,
                'part2_audio': part2_audio,
                'part3_audio': part3_audio,
                'session_id':  session_id,
            }.items() if not v
        ]
        if missing:
            return Response(
                {'status': False, 'error': f'Missing fields: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Load questions from DB using session_id
        try:
            question_set = QuestionSet.objects.get(id=session_id)
            questions = question_set.questions
            with transaction.atomic():
                SpeakingAnswer.objects.bulk_create([
                    SpeakingAnswer(session=question_set, part=1, audio=part1_audio),
                    SpeakingAnswer(session=question_set, part=2, audio=part2_audio),
                    SpeakingAnswer(session=question_set, part=3, audio=part3_audio),
                ])

        except QuestionSet.DoesNotExist:
            return Response(
                {'status': False, 'error': 'Invalid or expired session_id'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            task = Task.objects.get(user=request.user, module='speaking', question=session_id)
            if task.completed:
                return Response(
                    {'status': False, 'error': 'Speaking test already completed'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            task.completed = True
            task.save()
        except Task.DoesNotExist:
            return Response(
                {'status': False, 'error': 'Speaking task session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Transcribe all 3 audio files in parallel (~3× faster)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(get_transcript, part1_audio): 'part1',
                executor.submit(get_transcript, part2_audio): 'part2',
                executor.submit(get_transcript, part3_audio): 'part3',
            }
            transcripts = {}
            for future in as_completed(futures):
                key = futures[future]
                try:
                    transcripts[key] = future.result()
                except Exception as e:
                    return Response(
                        {'status': False, 'error': f'Transcription failed for {key}: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        # Evaluate with Gemini
        try:
            result = get_result(
                part1_transcript=transcripts['part1'],
                part2_transcript=transcripts['part2'],
                part3_transcript=transcripts['part3'],
                questions=questions,
            )
        except Exception as e:
            return Response(
                {'status': False, 'error': f'Evaluation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save result to the unified Results table
        count = Results.objects.filter(user=request.user, type='speaking').count() + 1
        Results.objects.create(
            user      = request.user,
            name      = f"Speaking Test {count}",
            score     = str(result.get('overall_band_score', '0.0')),
            type      = 'speaking',
            questions = questions, # The evaluation prompt's questions
            answers   = result     # The full AI feedback and transcripts
        )

        return Response({
            'status': True,
            'message': 'Speaking evaluated successfully',
            'transcripts': transcripts,
            'result': result,
        })

