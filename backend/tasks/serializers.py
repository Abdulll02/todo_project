from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Category
from django.utils import timezone

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.CharField(), 
        write_only=True, 
        required=False
    )
    category_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    created_date = serializers.DateTimeField(read_only=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False}
        }
    
    def validate_due_date(self, value):
        """Валидация дедлайна"""
        if value and value < timezone.now():
            raise serializers.ValidationError("Дедлайн не может быть в прошлом")
        return value
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        category_names = validated_data.pop('category_names', [])
        
        if 'user' not in validated_data and hasattr(self.context.get('request'), 'user'):
            validated_data['user'] = self.context['request'].user
        
        task = Task.objects.create(**validated_data)
        
        # Обрабатываем категории по ID
        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            task.categories.set(categories)
        
        # Обрабатываем категории по именам
        if category_names:
            categories = []
            for category_name in category_names:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'color': '#007bff'}
                )
                categories.append(category)
            task.categories.set(categories)
        
        return task
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        category_names = validated_data.pop('category_names', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if category_ids is not None:
            categories = Category.objects.filter(id__in=category_ids)
            instance.categories.set(categories)
        
        if category_names is not None:
            categories = []
            for category_name in category_names:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'color': '#007bff'}
                )
                categories.append(category)
            instance.categories.set(categories)
        
        return instance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']