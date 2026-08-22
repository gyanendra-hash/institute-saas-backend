from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsInstituteAdmin(BasePermission):
    message = "Only institute admins can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "teacher")
        )


class IsAdminOrReadOnly(BasePermission):
    """Admins can write; teachers/students/parents get read-only access."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "admin"
