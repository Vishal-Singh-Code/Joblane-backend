from rest_framework.permissions import BasePermission

class IsJobSeeker(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            request.user.is_authenticated and
            hasattr(user, "profile") and
            request.user.profile.role == 'jobseeker'
        )


class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            request.user.is_authenticated and
            hasattr(user, "profile") and
            request.user.profile.role == 'recruiter'
        )


class IsJobOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj can be Job OR Application
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user

        if hasattr(obj, "job"):
            return obj.job.created_by == request.user

        return False
