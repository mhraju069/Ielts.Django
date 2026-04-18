from rest_framework import generics, status, views
from rest_framework.response import Response
from django.db.models import Count
from .models import *
from .serializers import *
from .utils import *
from rest_framework.permissions import IsAuthenticated

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
                'message': 'Set ID and answers are required',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(answers, (list, dict)):
            return Response({
                'success': False,
                'message': 'Answers must be a dict or list',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


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
                'message': result if result else 'Failed to save reading answers',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        data = get_result(set_id, answers)

        result.score = data.get('raw_score', result.score)
        result.save()

        return Response({
            'success': True,
            'message': 'Reading answers submitted successfully',
            'data': data
        })
        
    