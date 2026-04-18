from django.contrib import admin
from .models import *
from unfold.admin import ModelAdmin

# Register your models here.

@admin.register(ReadingPassage)
class ReadingPassageAdmin(ModelAdmin):
    list_display = ('title', 'level', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('level',)


@admin.register(ReadingQuestion)
class ReadingQuestionAdmin(ModelAdmin):
    list_display = ('question_number', 'passage', 'question', 'question_type')
    autocomplete_fields = ('passage',)
    search_fields = ('question',)
    list_filter = ('question_type',)


@admin.register(QuestionSet)
class QuestionSetAdmin(ModelAdmin):
    readonly_fields = ('id', 'passages', 'answers')
    autocomplete_fields = ('passages',)


