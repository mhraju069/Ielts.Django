from django.urls import path
from .views import *

urlpatterns = [
    path('blogs/', BlogListView.as_view(), name='blog_list'),
    path('blog/<int:id>/', BlogDetailView.as_view(), name='blog_detail'),
    path('dashboard/', DashBoardView.as_view(), name='dashboard'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('message/', MessagesView.as_view(), name='message'),
]