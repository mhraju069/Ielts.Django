from django.urls import path
from .views import *

urlpatterns = [
    path('blogs/', BlogListView.as_view(), name='blog_list'),
    path('blog/<int:id>/', BlogDetailView.as_view(), name='blog_detail'),
]