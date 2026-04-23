from rest_framework import generics, status, views
from rest_framework.response import Response
from django.db.models import Count
from .models import *
from .serializers import *
from .utils import *
from rest_framework.permissions import IsAuthenticated
from others.models import Task
from subscriptions.models import Plan
# Create your views here.


class CreatePassageQuestionAnswerView(generics.ListCreateAPIView):
    queryset = ReadingPassage.objects.all()
    serializer_class = ReadingPassageSerializer

    def create(self, request, *args, **kwargs):
        if 'passages' in request.data and isinstance(request.data['passages'], list):
            serializer = self.get_serializer(data=request.data['passages'], many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        return super().create(request, *args, **kwargs)



class ReadingPassageListView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        count = request.user.results.filter(type='reading').count()
        plan = request.user.subscriptions.filter(active=True).first()
        
        if not plan or plan.plan.name == "free":
            free_plan = plan.plan if plan else Plan.objects.filter(name="free").first()
            limit = free_plan.test_limit if free_plan else 2 # default to 2 if something is missing
            
            if count >= limit:
                return Response({
                    "status": False,
                    "message": f"You have completed {limit} free reading tasks. Please upgrade your plan to continue."
                }, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = Task.objects.get(user=request.user, module='reading', completed=False)
            question_set = QuestionSet.objects.get(id=task.question)
            serializer = QuestionSetSerializer(question_set, context={'task': task})
            return Response({
                'success': True,
                'message': 'Reading test session created successfully',
                'data': serializer.data
            })
        except Task.DoesNotExist:
            question_set = create_question_set()
            serializer = QuestionSetSerializer(question_set)
            Task.objects.create(user=request.user, module='reading', question=question_set.id, completed=False)
            return Response({
                'success': True,
                'message': 'Reading test session created successfully',
                'data': serializer.data
            })



class ReadingQuestionAnswerSubmitView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
            
        set_id = data.get('set_id')
        answers = data.get('answers', [])

        if not set_id or not answers:
            return Response({
                'success': False,
                'log': 'Set ID and answers are required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(answers, (list, dict)):
            return Response({
                'success': False,
                'log': 'Answers must be a dict or list',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Task.objects.get(user=request.user, module='reading', question=set_id)

            task.completed = True
            task.save()

        except Task.DoesNotExist:
            return Response({
                'success': False,
                'log': 'Test not found',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        if isinstance(answers, list):
            merged = {}
            for item in answers:
                if isinstance(item, dict):
                    merged.update(item)
            answers = merged
        success, result = save_result(set_id, answers, request.user)

        if not success:
            return Response({
                'success': False,
                'log': result if result else 'Failed to save reading answers',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        data = get_result(set_id, answers)
        result.score = data.get('score', result.score)
        result.feedback = data
        result.save()
        data["id"] = result.id

        return Response({
            'success': True,
            'log': 'Reading answers submitted successfully',
            'data': data
        })
        
    