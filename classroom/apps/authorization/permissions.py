from rest_framework import permissions
from django.utils.translation import gettext_lazy as _

class IsVerified(permissions.BasePermission):
    message = _("Пользователь не верифицирован. Доступ запрещен.")
    
    def has_permission(self, request, view):
        return request.user.is_verified