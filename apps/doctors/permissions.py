from rest_framework import permissions


class IsDoctorManagerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission allowing any authenticated user to view doctors,
    but only the user who created/manages the doctor (or staff) to edit or delete.
    """
    message = "You do not have permission to modify or delete this doctor."

    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions (PUT, PATCH, DELETE) are restricted to the owner or staff
        if obj.created_by is None:
            # If created_by is unassigned, only staff can modify
            return request.user.is_staff
        return obj.created_by == request.user or request.user.is_staff
