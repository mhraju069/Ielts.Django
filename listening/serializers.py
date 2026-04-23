from rest_framework import serializers
from django.db import transaction
from .models import ListeningTask, Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question', 'answer']

class ListeningTaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ListeningTask
        fields = ['id', 'type', 'audio', 'questions', 'start', 'duration']

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

    @transaction.atomic
    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        task = ListeningTask.objects.create(**validated_data)
        
        # Create questions for the task
        for q_data in questions_data:
            Question.objects.create(task=task, **q_data)
            
        return task