from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Task, Category
from .serializers import TaskSerializer, CategorySerializer, UserSerializer

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Task.objects.all()
    
    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username='telegram_bot_user',
            defaults={'email': 'bot@example.com'}
        )
        serializer.save(user=user)

    @action(detail=True, methods=['post'])
    def delete_task(self, request, pk=None):
        try:
            task = self.get_object()
            task.delete()
            return Response({'message': 'Task deleted successfully'}, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def create_category(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delete_category(self, request, pk=None):
        try:
            category = self.get_object()
            category.delete()
            return Response({'message': 'Category deleted successfully'}, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def check_category(self, request):
        name = request.query_params.get('name', '')
        exists = Category.objects.filter(name__iexact=name).exists()
        return Response({'exists': exists})

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]