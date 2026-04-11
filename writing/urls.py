from django.urls import path
from .views import *

urlpatterns = [
    path('create/', WritingTaskCreateView.as_view(), name='create_writing_task'),
    path('tasks/', GetWritingTaskView.as_view(), name='get_writing_task'),
    path('submit/', WritingResultCreateView.as_view(), name='writing_result_submit'),
]