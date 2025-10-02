from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Task
import requests
import os

@shared_task
def check_due_tasks():
    now = timezone.now()
    due_tasks = Task.objects.filter(
        completed=False,
        due_date__lte=now,
        due_date__isnull=False
    )
    
    for task in due_tasks:
        send_task_notification.delay(task.id)

@shared_task
def send_task_notification(task_id):
    try:
        task = Task.objects.get(id=task_id)
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Здесь должна быть логика отправки уведомления в Telegram
        # Для простоты выведем в консоль
        print(f"Уведомление: Задача '{task.title}' просрочена!")
        
    except Task.DoesNotExist:
        pass