from django.db import models

# Create your models here.


class ListeningTask(models.Model):
    audio = models.FileField(upload_to='audio/')

    def __str__(self):
        return f"Listening Test {self.id}"


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
