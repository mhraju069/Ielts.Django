from django.db import models

# Create your models here.


import uuid
from datetime import timedelta

class ListeningTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=100, default="Listening Test")
    audio = models.FileField(upload_to='audio/')
    start = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(default=timedelta(minutes=40))

    def __str__(self):
        return f"{self.type} {self.id}"


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice (A, B, C)'),
        ('matching', 'Matching Items'),
        ("blank", "Blank Fill"),
    ]
    
    type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    task = models.ForeignKey(ListeningTask, on_delete=models.CASCADE, related_name='questions')
    question = models.JSONField(blank=True, null=True)
    answer = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.task.type} - {self.question[:50]}..."
