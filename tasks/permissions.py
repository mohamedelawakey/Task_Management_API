from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwner(BasePermission):
    """
    Access is only allowed to the task owner.
    All read/write access is restricted to the owner.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
