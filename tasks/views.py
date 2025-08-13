from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Task
from .serializers import TaskSerializer, UserSerializer
from .permissions import IsOwner
from .filters import TaskFilter
from django.utils import timezone

class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for users (for testing/admin). In production, permissions will likely be reduced.
    """
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD for tasks — Restricted to user tasks only.
    + Filters: status, priority, due_date_after/before
    + Sort: due_date, priority
    + Search (optional): title/description
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "priority", "created_at"]

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # POST /api/tasks/{id}/complete/
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.status == Task.Status.COMPLETED:
            return Response({"detail": "Task already completed."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save()
        return Response(TaskSerializer(task).data)

    # POST /api/tasks/{id}/incomplete/
    @action(detail=True, methods=["post"])
    def incomplete(self, request, pk=None):
        task = self.get_object()
        if task.status == Task.Status.PENDING:
            return Response({"detail": "Task already pending."}, status=status.HTTP_400_BAD_REQUEST)
        task.status = Task.Status.PENDING
        task.completed_at = None
        task.save()
        return Response(TaskSerializer(task).data)
