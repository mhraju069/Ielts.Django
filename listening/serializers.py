from rest_framework import serializers
from django.db import transaction
from .models import ListeningTask, Question

class QuestionSerializer(serializers.ModelSerializer):
    question_type = serializers.CharField(write_only=True, required=False)
    level = serializers.IntegerField(write_only=True, required=False)
    question_number = serializers.IntegerField(write_only=True, required=False)
    options = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = Question
        fields = ['id', 'question', 'answer', 'type', 'question_type', 'level', 'question_number', 'options']
        extra_kwargs = {
            'type': {'required': False},
            'question': {'required': False},
            'answer': {'required': False},
        }

class ListeningTaskSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField(read_only=True)
    audio = serializers.FileField(required=False, allow_null=True)
    questions = serializers.JSONField(required=False)
    answers = serializers.JSONField(required=False,write_only=True)
    
    class Meta:
        model = ListeningTask
        fields = ['id', 'audio', 'questions', 'duration', 'answers']

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

    def to_internal_value(self, data):
        # Convert to a mutable dict to avoid deepcopy issues with file objects in QueryDict
        if hasattr(data, 'dict'):
            data = data.dict()
        else:
            # Create a shallow copy if it's already a dict
            data = data.copy()

        # Handle cases where data might be from multipart form-data
        # where lists/dicts are sent as JSON strings
        if 'questions' in data and isinstance(data['questions'], str):
            import json
            try:
                data['questions'] = json.loads(data['questions'])
            except ValueError:
                pass

        # If audio is a string (e.g. "test2.mp3"), we treat it as a placeholder
        if 'audio' in data and isinstance(data['audio'], str):
            data['audio'] = None # Placeholder
            
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        
        # Prepare aggregated questions and answers for storage in ListeningTask
        all_questions = []
        all_answers = {}
        
        task = ListeningTask.objects.create(**validated_data)
        
        for q_data in questions_data:
            # Map user format to model fields
            q_type = q_data.get('question_type', q_data.get('type', 'mcq'))
            if q_type == 'mcq':
                model_type = 'mcq'
            elif q_type == 'match':
                model_type = 'matching'
            elif q_type == 'fill_in_the_blank':
                model_type = 'blank'
            else:
                model_type = q_type

            # Prepare the question JSON
            question_content = q_data.get('question', {})
            if isinstance(question_content, str):
                question_content = {'text': question_content}
            
            # Merge extra fields into question JSON
            q_json = {
                'text': question_content.get('text', q_data.get('question')),
                'level': q_data.get('level'),
                'question_number': q_data.get('question_number'),
                'options': q_data.get('options'),
                'type': model_type
            }
            
            # Store individual question model
            Question.objects.create(
                task=task,
                type=model_type,
                question=q_json,
                answer=q_data.get('answer')
            )
            
            # Add to aggregated lists
            all_questions.append(q_json)
            if q_data.get('question_number'):
                all_answers[str(q_data.get('question_number'))] = q_data.get('answer')
            
        # Update task with aggregated data
        task.questions = all_questions
        task.answers = all_answers
        task.save()
            
        return task