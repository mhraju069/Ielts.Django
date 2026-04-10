from rest_framework import generics, status, views
from rest_framework.response import Response
from django.db.models import Count
from .models import *
from .serializers import *
from .utils import *

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
    def get(self, request):
        set_id, queryset = get_reading_passage_queryset()

        # Pass the set_id to the serializer via context
        serializer = ReadingPassageListSerializer(
            queryset, 
            many=True, 
        )
        
        return Response({
            'success': True,
            'message': 'Reading passages fetched successfully',
            'set': set_id,
            'data': serializer.data
        })