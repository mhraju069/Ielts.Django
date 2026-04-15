from django.urls import path
from .views import *

urlpatterns = [
    path('session/', GenerateSpeakingSessionView.as_view(), name='speaking-session'),
    path('result/', SpeakingResultView.as_view(), name='speaking-result'),
]
