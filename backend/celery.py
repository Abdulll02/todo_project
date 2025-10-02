import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo.settings')

app = Celery('todo')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-due-tasks': {
        'task': 'tasks.tasks.check_due_tasks',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}