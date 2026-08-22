import threading
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

_thread_locals = threading.local()


def get_current_tenant():
    return getattr(_thread_locals, "tenant", None)


def set_current_tenant(tenant):
    _thread_locals.tenant = tenant


class TenantMiddleware(MiddlewareMixin):
    """Resolves the tenant from the subdomain on every request.

    e.g. abc.yoursaas.com -> Tenant.objects.get(slug='abc')
    Skips resolution for platform-level hosts (www, localhost, api) and for
    Render's default *.onrender.com host — that's a single fixed hostname
    with no wildcard DNS, so it can't carry a tenant subdomain until a real
    custom domain is attached (Deployment Guide §3.6).
    """

    EXEMPT_SUBDOMAINS = {"www", "localhost", "127", "api", "admin"}
    EXEMPT_HOST_SUFFIXES = (".onrender.com",)

    def process_request(self, request):
        host = request.get_host().split(":")[0]

        if host in ("localhost", "127.0.0.1") or host.endswith(self.EXEMPT_HOST_SUFFIXES):
            request.tenant = None
            set_current_tenant(None)
            return None

        subdomain = host.split(".")[0]
        if subdomain in self.EXEMPT_SUBDOMAINS:
            request.tenant = None
            set_current_tenant(None)
            return None

        try:
            tenant = Tenant.objects.get(slug=subdomain, is_active=True)
        except Tenant.DoesNotExist:
            return HttpResponseForbidden("Invalid or inactive tenant.")

        request.tenant = tenant
        set_current_tenant(tenant)
        return None

    def process_response(self, request, response):
        set_current_tenant(None)  # prevent thread-local leakage across requests
        return response
