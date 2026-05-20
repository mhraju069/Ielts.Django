from django.utils import timezone
from celery import shared_task

@shared_task
def clean_pending_payments():
    """Clean up pending payments older than 1 day"""
    from django.apps import apps
    Payments = apps.get_model('payments', 'Payments')
    payments = Payments.objects.filter(status='pending', created_at__lt=timezone.now() - timezone.timedelta(days=1))
    print(f"Found {payments.count()} pending payments to clean up")
    for payment in payments:
        payment.delete()
    print(f"Cleaned up {payments.count()} pending payments")

    
@shared_task
def check_expired_subscriptions():
    """Check for expired subscriptions, deactivate them, and reset to free plan"""
    from django.apps import apps
    from django.utils import timezone
    Subscriptions = apps.get_model('subscriptions', 'Subscriptions')
    Plan = apps.get_model('subscriptions', 'Plan')
    
    # 1. Find active subscriptions that have an end date in the past
    expired_subs = Subscriptions.objects.filter(
        active=True, 
        end__lt=timezone.now()
    ).exclude(plan__duration='permanent')
    
    count = expired_subs.count()
    if count > 0:
        # We need to process them individually to ensure they get a free plan
        free_plan = Plan.objects.filter(name='free').first()
        
        for sub in expired_subs:
            user = sub.user
            sub.active = False
            sub.save()
            
            # Check if user already has an active free plan (safety check)
            if free_plan and not Subscriptions.objects.filter(user=user, plan=free_plan, active=True).exists():
                Subscriptions.objects.create(
                    user=user,
                    plan=free_plan,
                    active=True
                )
        
        print(f"Processed {count} expired subscriptions and reset to free plan")
    
    return f"Processed {count} expired subscriptions"
