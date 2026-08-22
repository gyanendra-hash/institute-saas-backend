from django.contrib.auth.backends import ModelBackend
from apps.tenants.middleware import get_current_tenant
from .models import User


class TenantAwareAuthBackend(ModelBackend):
    """Login must look up the user WITHIN the resolved tenant, but bypasses
    User.objects (tenant-scoped manager) directly querying all_objects with
    an explicit tenant filter — avoids relying on thread-local timing."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        tenant = get_current_tenant()
        qs = User.all_objects.filter(username=username)
        if tenant:
            qs = qs.filter(tenant=tenant)

        try:
            user = qs.get()
        except User.DoesNotExist:
            User().set_password(password)  # timing-attack mitigation
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.all_objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
