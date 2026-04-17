from celery import Celery

app = Celery('ielts')
app.config_from_object('core.settings', namespace='CELERY')
app.autodiscover_tasks(['core'])

app.conf.beat_schedule = {
    'clean-pending-payments': {
        'task': 'core.task.clean_pending_payments',
        'schedule': 3600,  # 1 hour
    },
}
