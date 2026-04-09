from django.urls import path
from .views import *

urlpatterns = [
    path('create/', CreatePassageQuestionAnswerView.as_view(), name='create_passage_question_answer'),
    path('passage/', ReadingPassageListView.as_view(), name='reading_passage_list'),
]