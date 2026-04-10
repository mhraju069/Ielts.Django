from rest_framework import serializers
from django.db import transaction
from .models import *



class WritingTaskListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        tasks = [WritingTask(**item) for item in validated_data]
        return WritingTask.objects.bulk_create(tasks)



class WritingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTask
        fields = ['id', 'title', 'type', 'question', 'level', 'image']
        list_serializer_class = WritingTaskListSerializer

