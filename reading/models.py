from django.db import models

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
        ('match', 'Matching Headings'),
        ('answer', 'Answer the questions'),
    ]

    passage = models.ForeignKey(ReadingPassage, on_delete=models.CASCADE, related_name='questions')
    question_number = models.IntegerField(null=True, blank=True)
    question = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    options = models.JSONField(null=True, blank=True)
    answer = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Q{self.question_number} [{self.question_type}]: {self.question[:50]}"

    class Meta:
        verbose_name = 'Reading Question'
        verbose_name_plural = 'Reading Questions'