from django.db import models
from django.contrib.auth import get_user_model
import uuid
User = get_user_model()
from ckeditor.fields import RichTextField
# Create your models here.

class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = RichTextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title




class Results(models.Model):
    RESULT_TYPES = (
        ('reading', 'Reading'),
        ('writing', 'Writing'),
        ('listening', 'Listening'),
        ('speaking', 'Speaking'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results')
    name = models.CharField(max_length=100)
    score = models.CharField(max_length=10, default="0.0")
    type = models.CharField(max_length=100, choices=RESULT_TYPES)
    questions = models.JSONField(blank=True, null=True)
    answers = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name