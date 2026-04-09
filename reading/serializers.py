from rest_framework import serializers
from django.db import transaction
from .models import ReadingPassage, ReadingQuestion


class ReadingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuestion
        fields = ['id', 'question_number', 'question', 'question_type', 'options', 'answer']


class ReadingPassageSerializer(serializers.ModelSerializer):
    questions = ReadingQuestionSerializer(many=True)

    class Meta:
        model = ReadingPassage
        fields = ['id', 'title', 'content', 'level', 'questions']

    @transaction.atomic
    def create(self, validated_data):
        questions_data = validated_data.pop('questions')

        # Passage create
        passage = ReadingPassage.objects.create(**validated_data)

        # Bulk question create
        question_objs = [
            ReadingQuestion(passage=passage, **q)
            for q in questions_data
        ]
        ReadingQuestion.objects.bulk_create(question_objs)

        return passage