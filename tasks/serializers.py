from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class TaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "owner", "title", "description",
            "due_date", "priority", "status",
            "created_at", "completed_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "completed_at"]

    def validate_due_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Due date must be today or in the future.")
        return value

    def validate_priority(self, value):
        allowed = {c[0] for c in Task.Priority.choices}
        if value not in allowed:
            raise serializers.ValidationError(f"Priority must be one of: {', '.join(allowed)}")
        return value

    def validate(self, data):
        """
        Prevent modification of a completed task unless we return it pending.
        - During update: If an instance exists and its status is completed and the user hasn't requested to return it pending,
        prevent any modification of other fields.
        """
        instance = getattr(self, "instance", None)
        if instance:
            was_completed = (instance.status == Task.Status.COMPLETED)
            will_completed = data.get("status", instance.status) == Task.Status.COMPLETED
            will_pending = data.get("status", instance.status) == Task.Status.PENDING

            if was_completed and not will_pending:
                # He wants to edit something without returning it to pending
                # If he tries to leave it completed and edit anything -> forbidden
                changed_fields = {k for k in data.keys() if data.get(k) != getattr(instance, k, None)}
                if changed_fields:
                    raise serializers.ValidationError(
                        "Completed tasks cannot be edited unless you revert status to 'pending'."
                    )

            # Seal of Completion
            if not was_completed and will_completed:
                data["completed_at"] = timezone.now()
            if was_completed and will_pending:
                data["completed_at"] = None

        else:
            # create: If status=completed, put completed_at
            if data.get("status") == Task.Status.COMPLETED:
                data["completed_at"] = timezone.now()

        return data
