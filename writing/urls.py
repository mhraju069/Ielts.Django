from django.urls import path
from .views import *

urlpatterns = [
    path('create/', WritingTaskCreateView.as_view(), name='create_writing_task'),
    path('tasks/', GetWritingTaskView.as_view(), name='get_writing_task'),
    # path('submit/', ReadingQuestionAnswerSubmitView.as_view(), name='reading_question_answer_submit'),
]