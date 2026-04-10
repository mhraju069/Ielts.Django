from .serializers import *
from .models import *
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
