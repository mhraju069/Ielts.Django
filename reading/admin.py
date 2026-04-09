from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin

# Register your models here.

admin.site.register(ReadingPassage, ModelAdmin)
admin.site.register(ReadingQuestion, ModelAdmin)