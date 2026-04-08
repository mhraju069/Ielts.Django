from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework import generics, status, permissions
from rest_framework.response import Response

# Create your views here.



class BlogListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BlogSerializer
    queryset = Blog.objects.all().order_by('-created_at')



class BlogDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BlogSerializer
    queryset = Blog.objects.all()
    lookup_field = 'id'