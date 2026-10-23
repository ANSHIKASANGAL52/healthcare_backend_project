from rest_framework import permissions


class IsPatientOwner(permissions.BasePermission):
    """
    Object-level permission to only allow the user who created the patient (or staff)
    to view, edit, or delete the patient record.
    Prevents IDOR (Insecure Direct Object Reference).
    """

    def has_object_permission(self, request, view, obj):
        # Only the creator of the patient or staff is authorized
        return obj.created_by == request.user or request.user.is_staff
