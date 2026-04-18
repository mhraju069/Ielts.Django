from rest_framework import serializers
from django.db import transaction
from .models import *



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
    class Meta:
        model = WritingTask
        fields = ['id', 'question', 'start', 'duration']

