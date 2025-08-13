from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "-priority"]  

    def clean(self):
        # due_date must be in the future or today
        if self.due_date < timezone.localdate():
            raise ValidationError({"due_date": "Due date must be today or in the future."})

        # If it's complete and you're trying to edit it without returning it to pending — we'll block it in the serializer.
        # Here, just make sure that completed_at is compatible with status.
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status == self.Status.PENDING and self.completed_at:
            # If we return it pending, delete the completion stamp
            self.completed_at = None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.status})"
