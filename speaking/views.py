from rest_framework import generics, views, status
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import *
from .utils import generate_speaking_questions, get_transcript, get_result
from django.db import transaction
from others.models import Results
from rest_framework.permissions import IsAuthenticated



class GenerateSpeakingSessionView(views.APIView):
    def get(self, request):
        try:
            questions = generate_speaking_questions()

            session = QuestionSet.objects.create(questions=questions)

            return Response({
                'status': True,
                'session_id': str(session.id),
                **questions,
            })
        except Exception as e:
            return Response(
                {'status': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




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

            if question_set.is_ended():
                return Response(
                    {'status': False, 'error': 'Test has ended'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except QuestionSet.DoesNotExist:
            return Response(
                {'status': False, 'error': 'Invalid or expired session_id'},
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

