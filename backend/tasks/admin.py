from django.contrib import admin
from .models import Task, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']
    search_fields = ['name']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'completed', 'due_date', 'created_date']
    list_filter = ['completed', 'categories', 'created_date']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']