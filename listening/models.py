from django.db import models

# Create your models here.


import uuid
from datetime import timedelta

class ListeningTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio = models.FileField(upload_to='audio/', null=True, blank=True)
    duration = models.DurationField(default=timedelta(minutes=40))
    questions = models.JSONField(blank=True, null=True)
    answers = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Listening Task {self.id}"


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice (A, B, C)'),
        ('matching', 'Matching Items'),
        ("blank", "Blank Fill"),
    ]
    
    type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    task = models.ForeignKey(ListeningTask, on_delete=models.CASCADE, related_name='task_questions')
    question = models.JSONField(blank=True, null=True)
    answer = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} {self.id}"
