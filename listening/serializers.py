from rest_framework import serializers
from django.db import transaction
from .models import ListeningTask, Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question', 'answer']

class ListeningTaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    
    class Meta:
        model = ListeningTask
        fields = ['id', 'type', 'audio', 'questions']

    @transaction.atomic
    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        task = ListeningTask.objects.create(**validated_data)
        
        # Create questions for the task
        for q_data in questions_data:
            Question.objects.create(task=task, **q_data)
            
        return task