from django.urls import path
from .views import *

urlpatterns = [
    path('create/', ListeningTaskListView.as_view(), name='create_listening_task'),
    path('task/', ListeningTaskDetailView.as_view(), name='listening_task'),
    path('submit/', ListeningQuestionAnswerSubmitView.as_view(), name='submit_listening_answer'),
]