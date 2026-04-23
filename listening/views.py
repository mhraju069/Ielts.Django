import random
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ListeningTask, Question
from .serializers import ListeningTaskSerializer, QuestionSerializer
from others.models import Task



class ListeningTaskListView(generics.ListCreateAPIView):
    queryset = ListeningTask.objects.all()
    serializer_class = ListeningTaskSerializer

    def create(self, request, *args, **kwargs):
        # Check if the data is a list for bulk creation
        is_many = isinstance(request.data, list)
        
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ListeningTaskDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = request.user.results.filter(type='listening').count()
        plan = request.user.subscriptions.first()
        
        if plan and plan.plan.name == "free":
            if count >= plan.plan.test_limit:
                return Response({
                    "status": False,
                    "message": f"You have completed {plan.plan.test_limit} free listening tasks. Please upgrade your plan to continue."
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = Task.objects.get(user=request.user, module='listening', completed=False)
            listening_task = ListeningTask.objects.get(id=task.question)
            serializer = ListeningTaskSerializer(listening_task, context={'task': task})
            return Response({
                'success': True,
                'message': 'Listening test session retrieved successfully',
                'data': serializer.data
            })
        except Task.DoesNotExist:
            listening_task = ListeningTask.objects.order_by('?').first()
            if not listening_task:
                return Response({
                    'success': False,
                    'message': 'No listening tasks available',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
                
            task = Task.objects.create(user=request.user, module='listening', question=listening_task.id, completed=False)
            serializer = ListeningTaskSerializer(listening_task, context={'task': task})
            return Response({
                'success': True,
                'message': 'Listening test session created successfully',
                'data': serializer.data
            })
