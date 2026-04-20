from rest_framework import serializers
from django.db import transaction
from .models import ReadingPassage, ReadingQuestion, QuestionSet



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



class ReadingQuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQuestion
        fields = ['question_number', 'question', 'question_type', 'options']



class ReadingPassageListSerializer(serializers.ModelSerializer):
    questions = ReadingQuestionListSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReadingPassage
        exclude = ['created_at', 'updated_at']



class QuestionSetSerializer(serializers.ModelSerializer):
    passages = ReadingPassageListSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionSet
        fields = ['id', 'passages', 'start', 'duration']

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
