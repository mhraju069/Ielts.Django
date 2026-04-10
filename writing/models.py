from django.db import models

# Create your models here.


class WritingTask(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=[('graph', 'Graph'),('text', 'Text')])
    question = models.TextField()
    level = models.IntegerField(choices=[(1, '1'), (2, '2')])
    image = models.ImageField(upload_to='writing-task/', null=True, blank=True)

    def __str__(self):
        return f"Level {self.level} - {self.title}"