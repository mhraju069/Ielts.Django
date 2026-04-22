from django.db import models
import uuid
from datetime import timedelta
from django.utils import timezone
# Create your models here.


class QuestionSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    questions = models.JSONField()
    start = models.DateTimeField(default=timezone.now)
    duration = models.DurationField(default=timedelta(minutes=14))

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'Question Set'
        verbose_name_plural = 'Question Sets'




class SpeakingAnswer(models.Model):
    session = models.ForeignKey(QuestionSet, on_delete=models.CASCADE, related_name='answers')
    part = models.IntegerField(choices=[(1, 'Part 1'), (2, 'Part 2'), (3, 'Part 3')],default=1)
    audio = models.FileField(upload_to='speaking_answers/',blank=True,null=True)
    transcript = models.TextField(blank=True,null=True)

    def __str__(self):
        return f"Answer - Part {self.part} - {self.session.id}"
