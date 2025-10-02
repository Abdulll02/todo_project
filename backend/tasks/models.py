import hashlib
import time
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone

class CustomPKModel(models.Model):
    class Meta:
        abstract = True

    def generate_pk(self):
        """Не статический метод, а обычный метод экземпляра"""
        timestamp = str(time.time_ns())
        random_component = hashlib.sha256(timestamp.encode()).hexdigest()[:16]
        return f"{timestamp}_{random_component}"

    def save(self, *args, **kwargs):
        """Переопределяем save для генерации ID перед сохранением"""
        if not self.pk:
            self.pk = self.generate_pk()
        super().save(*args, **kwargs)

    id = models.CharField(
        primary_key=True,
        max_length=50,
        editable=False
    )

class Category(CustomPKModel):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # HEX color
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Task(CustomPKModel):
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    completed = models.BooleanField(default=False, verbose_name='Выполнено')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')
    created_date = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    categories = models.ManyToManyField(Category, blank=True, verbose_name='Категории')
    
    def clean(self):
        """Валидация дат"""
        if self.due_date and self.due_date < timezone.now():
            raise ValidationError({'due_date': 'Дедлайн не может быть в прошлом'})
        
        if self.due_date and self.due_date < self.created_date:
            raise ValidationError({'due_date': 'Дедлайн не может быть раньше даты создания'})
    
    def save(self, *args, **kwargs):
        """Переопределяем save для вызова валидации"""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """Проверка просрочена ли задача"""
        if self.due_date and not self.completed:
            return self.due_date < timezone.now()
        return False
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'