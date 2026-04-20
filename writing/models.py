from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
import uuid
# Create your models here.


class WritingQuestion(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=[('graph', 'Graph'),('text', 'Text')])
    question = models.TextField()
    level = models.IntegerField(choices=[(1, '1'), (2, '2')])
    image = models.ImageField(upload_to='writing-task/', null=True, blank=True)

    def __str__(self):
        return f"Level {self.level} - {self.title}"




class WritingTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ManyToManyField(WritingQuestion, related_name='writing_tasks')
    start = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(default=timedelta(minutes=60))
    
    def __str__(self):
        return f"Task {self.id}"
    
    def is_ended(self):
        return timezone.now() > (self.start + self.duration + timedelta(minutes=3))