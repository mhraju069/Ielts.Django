from subscriptions.models import Subscriptions, Plan
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from django.utils import timezone

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        plan = Plan.objects.filter(name="free").first()
        if plan:
            Subscriptions.objects.create(user=instance, plan=plan, active=True)