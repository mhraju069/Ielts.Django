from django.db import models
from django.conf import settings
# Create your models here.


class WritingTask(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=[('graph', 'Graph'),('text', 'Text')])
    question = models.TextField()
    level = models.IntegerField(choices=[(1, '1'), (2, '2')])
    image = models.ImageField(upload_to='writing-task/', null=True, blank=True)

    def __str__(self):
        return f"Level {self.level} - {self.title}"



class WritingResult(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tasks = models.ManyToManyField(WritingTask)
    responses = models.JSONField()
    score = models.TextField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.score}"
