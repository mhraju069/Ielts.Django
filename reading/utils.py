from .models import ReadingPassage
from django.db.models import Q


def get_reading_passage_queryset(request):
    # Fetch one random passage for each level to form a set
    p1 = ReadingPassage.objects.filter(level=1).order_by('?').first()
    p2 = ReadingPassage.objects.filter(level=2).order_by('?').first()
    p3 = ReadingPassage.objects.filter(level=3).order_by('?').first()

    # Get IDs of the passages that exist
    ids = [p.id for p in [p1, p2, p3] if p]
    
    # Return a queryset containing these passages
    return ReadingPassage.objects.filter(id__in=ids).prefetch_related('questions')