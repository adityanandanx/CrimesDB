from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model
from .models import Case, Incident

User = get_user_model()


class RolePermission(BasePermission):
    """Enforce role-based access:
    - admin: all
    - viewer: read only
    - officer: can create incidents (POST /incidents)
    - investigator: can modify cases they lead or are assigned to
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == "admin":
            return True
        if user.role == "viewer":
            return request.method in SAFE_METHODS
        if user.role == "officer":
            # allow creating incidents and reading
            if view.basename == "incident" and request.method == "POST":
                return True
            return request.method in SAFE_METHODS
        if user.role == "investigator":
            # general read allowed
            return True if request.method in SAFE_METHODS else True
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == "admin":
            return True
        if user.role == "viewer":
            return request.method in SAFE_METHODS
        if isinstance(obj, Incident):
            if user.role == "officer":
                return request.method in SAFE_METHODS or request.method == "POST"
            return True  # investigators can read
        if isinstance(obj, Case):
            if request.method in SAFE_METHODS:
                return True
            if user.role == "officer":
                return False
            if user.role == "investigator":
                lead_id = getattr(obj, "lead_investigator_id", None)
                if lead_id == user.id:
                    return True
                assignments = getattr(obj, "assignments", None)
                if assignments is not None:
                    return assignments.filter(user=user).exists()
                return False
        return False
