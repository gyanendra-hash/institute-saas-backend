from django.db import models
from .middleware import get_current_tenant


class TenantManager(models.Manager):
    """Auto-scopes querysets to the current request's tenant. Fail-safe: returns
    an empty queryset (never all-tenant data) when no tenant is resolved."""

    def get_queryset(self):
        tenant = get_current_tenant()
        qs = super().get_queryset()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs.none()

    def all_tenants(self):
        """Explicit escape hatch for platform-admin / cross-tenant use only."""
        return super().get_queryset()
