from django.db import models
from django.contrib.auth.models import User
import uuid
# Create your models here.



class ReadingPassage(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    level = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Reading Passage'
        verbose_name_plural = 'Reading Passages'



class ReadingQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice Question'),
        ('bool', 'True False or Not Given'),
        ('blank', 'Fill in the blanks'),
        ('match', 'Matching'),
        ('answer', 'Answer the questions'),
    ]

    passage = models.ForeignKey(ReadingPassage, on_delete=models.CASCADE, related_name='questions')
    question_number = models.IntegerField(null=True, blank=True)
    question = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    options = models.JSONField(null=True, blank=True, help_text="""For type 'MCQ':- ["a", "b", "c", "d"],    For type 'True/False/Not Given':- ["True", "False", "Not Given"],   For type 'Fill in the blanks':- null,    For type 'Matching':- {"left":["1", "2", "3"], "right":["a", "b", "c"]},    For type 'Answer the questions':- null""")
    answer = models.JSONField(null=True, blank=True, help_text="""For type 'Matching':- {"1": "a", "2": "b", "3": "c"},    For others: "Text" """)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q{self.question_number} [{self.question_type}]: {self.question[:50]}"

    class Meta:
        verbose_name = 'Reading Question'
        verbose_name_plural = 'Reading Questions'



class QuestionSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passages = models.ManyToManyField(ReadingPassage)
    answers = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Question Set {self.id}"

    class Meta:
        verbose_name = 'Question Set'
        verbose_name_plural = 'Question Sets'



class ReadingResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    set = models.ForeignKey(QuestionSet, on_delete=models.CASCADE)
    answers = models.JSONField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title or 'No Title'} ({self.score})"

    class Meta:
        verbose_name = 'Reading Result'
        verbose_name_plural = 'Reading Results'

    def save(self, *args, **kwargs):
        if not self.title:
            serial = ReadingResult.objects.filter(user=self.user).count()
            self.title = f"Reading Test {serial + 1}"
        super().save(*args, **kwargs)

