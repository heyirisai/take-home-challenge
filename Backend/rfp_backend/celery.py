import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rfp_backend.settings')

app = Celery('rfp_generator')

# Load config from Django settings with 'CELERY' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working"""
    print(f'Request: {self.request!r}')


# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'clean-expired-tasks': {
        'task': 'questions.tasks.clean_expired_tasks',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
