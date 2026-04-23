from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework import generics, status, permissions, views
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

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



class DashBoardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        results = Results.objects.filter(user=user).order_by('-created_at')
        
        # Get latest results for each module
        reading = results.filter(type='reading').first()
        writing = results.filter(type='writing').first()
        listening = results.filter(type='listening').first()
        speaking = results.filter(type='speaking').first()

        def get_band(res):
            if not res: return 0.0
            try:
                val = float(res.score)
                # If score is > 9, it's likely a raw score (e.g. 28/40), convert to band
                if val > 9:
                    if val >= 39: return 9.0
                    if val >= 37: return 8.5
                    if val >= 35: return 8.0
                    if val >= 33: return 7.5
                    if val >= 30: return 7.0
                    if val >= 27: return 6.5
                    if val >= 23: return 6.0
                    if val >= 19: return 5.5
                    if val >= 15: return 5.0
                    return 4.5
                return val
            except:
                return 0.0

        scores = [get_band(reading), get_band(writing), get_band(listening), get_band(speaking)]
        valid_scores = [s for s in scores if s > 0]
        avg_band = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0.0

        # Current Month Data
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_results = results.filter(created_at__gte=start_of_month)

        # Chart 1: Weekly Overall Band (Current Month)
        weekly_chart = []
        for i in range(4):
            w_start = start_of_month + timedelta(days=i*7)
            w_end = w_start + timedelta(days=7)
            if i == 3: # Include rest of the month in the last week
                if now.month == 12:
                    next_month = now.replace(year=now.year+1, month=1, day=1)
                else:
                    next_month = now.replace(month=now.month+1, day=1)
                w_end = next_month
            
            w_results = monthly_results.filter(created_at__range=[w_start, w_end])
            w_bands = [get_band(r) for r in w_results]
            w_avg = round(sum(w_bands) / len(w_bands), 1) if w_bands else 0.0
            weekly_chart.append({
                "week": f"Week {i+1}",
                "avg_band": w_avg
            })

        # Chart 2: Monthly Module Averages
        module_chart = []
        for m_type in ['reading', 'writing', 'listening', 'speaking']:
            m_results = monthly_results.filter(type=m_type)
            m_bands = [get_band(r) for r in m_results]
            m_avg = round(sum(m_bands) / len(m_bands), 1) if m_bands else 0.0
            module_chart.append({
                "module": m_type.capitalize(),
                "avg_band": m_avg
            })

        data = {
            "user": {
                "name": user.name or user.email,
                "image": request.build_absolute_uri(user.image.url) if user.image else None,
                "overall_band": avg_band,
            },
            "charts": {
                "weekly_overall": weekly_chart,
                "module_averages": module_chart
            },
            "recent_activities": [
                {
                    "name" : res.name,
                    "score" : res.score,
                    "created_at" : res.created_at,
                    
                } for res in results[:5]
            ]
        }
        
        return Response(data)
    



class MessagesView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        if not name or not email or not message:
            return Response(
                {'status': False, 'error': 'Missing fields'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        Messages.objects.create(
            name=name,
            email=email,
            message=message,
        )
        
        return Response({
            "status": True,
            "log": "Message sent successfully"
        })





class ContactView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = ContactInfo.objects.all().first()
        return Response({
            "status": True,
            "data": {
                "email": data.email or "",
                "phone": data.phone or "",
                "address": data.address or "",
                "support_timing": data.support_timing or "",
            }
        })

