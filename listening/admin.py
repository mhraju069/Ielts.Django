from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin

# Register your models here.

admin.site.register(ListeningTask, ModelAdmin)
admin.site.register(Question, ModelAdmin)