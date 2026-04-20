from rest_framework import serializers
from django.db import transaction
from .models import *
from others.models import Task



class WritingQuestionListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        questions = [WritingQuestion(**item) for item in validated_data]
        return WritingQuestion.objects.bulk_create(questions)


class WritingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingQuestion
        fields = ['id', 'title', 'type', 'question', 'level', 'image']
        list_serializer_class = WritingQuestionListSerializer


class WritingTaskSerializer(serializers.ModelSerializer):
    question = WritingQuestionSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WritingTask
        fields = ['id', 'question', 'start', 'duration']


    def get_duration(self, obj):
        try:
            time = self.context['task'].remaining_time()
            total_seconds = int(time.total_seconds())
            if total_seconds <= 0:
                return "00:00:00"
        except:
            total_seconds = int(obj.duration.total_seconds())
            
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}" 

        

