from rest_framework import generics, status
from rest_framework.response import Response
from .models import ListeningTask, Question
from .serializers import ListeningTaskSerializer, QuestionSerializer



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

class ListeningTaskDetailView(generics.RetrieveAPIView):
    queryset = ListeningTask.objects.all()
    serializer_class = ListeningTaskSerializer
