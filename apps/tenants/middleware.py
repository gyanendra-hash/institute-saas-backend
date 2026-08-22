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
    Skips resolution for platform-level hosts (www, localhost, api).
    """

    EXEMPT_SUBDOMAINS = {"www", "localhost", "127", "api", "admin"}

    def process_request(self, request):
        host = request.get_host().split(":")[0]
        subdomain = host.split(".")[0]

        if subdomain in self.EXEMPT_SUBDOMAINS or host in ("localhost", "127.0.0.1"):
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
