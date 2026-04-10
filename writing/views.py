from .serializers import *
from .models import *
from .utils import *
from rest_framework import generics, status, views
from rest_framework.response import Response




class WritingTaskCreateView(generics.ListCreateAPIView):
    queryset = WritingTask.objects.all()
    serializer_class = WritingTaskSerializer

    def create(self, request, *args, **kwargs):
        # Check if the data is a list (direct list or nested under 'tasks' key)
        is_many = isinstance(request.data, list)
        data = request.data
        
        if not is_many and 'tasks' in request.data and isinstance(request.data['tasks'], list):
            is_many = True
            data = request.data['tasks']
        
        if is_many:
            serializer = self.get_serializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        return super().create(request, *args, **kwargs)




class GetWritingTaskView(views.APIView):
    def get(self, request):
        queryset = WritingTask.objects.all()
        task1 = queryset.filter(level=1).order_by('?').first()
        task2 = queryset.filter(level=2).order_by('?').first()
        
        # We need to serialize the model instances before returning them in the response
        tasks = [task for task in [task1, task2] if task is not None]
        serializer = WritingTaskSerializer(tasks, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)




class WritingResultCreateView(views.APIView):
    def post(self, request, *args, **kwargs):
        answers = request.data.get('answers', [])
        task_ids = request.data.get('task', [])
        

        if not answers or not task_ids:
            return Response({"status": False, "message": "Answers and task are required"}, status=status.HTTP_400_BAD_REQUEST)

        result = get_result(answers, task_ids)
        score_val = result['score'] if result and 'score' in result else "0.0"

        obj = WritingResult.objects.create(
            user=request.user,
            score=score_val,
            responses=result['answers']
        )

        if isinstance(task_ids, list):
            obj.tasks.set(task_ids)
        else:  
            obj.tasks.add(task_ids)
        
        count = WritingResult.objects.filter(user=request.user).count()
        obj.title = f"Writing Test {count}"
        obj.save()


        return Response({
            "status": True, 
            "message": "Result saved successfully", 
            "result": result
        }, status=status.HTTP_201_CREATED)
        
        