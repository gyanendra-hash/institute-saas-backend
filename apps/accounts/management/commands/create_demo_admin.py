import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.tenants.models import Tenant


class Command(BaseCommand):
    """Idempotently creates one demo tenant + admin login, so a fresh
    deployment has a working account without dashboard/SSH access. No-ops
    unless DEMO_ADMIN_USERNAME and DEMO_ADMIN_PASSWORD are both set, so it
    never creates an unattended account as a side effect of a normal build.
    """

    help = "Create (or reset) a demo tenant admin from DEMO_ADMIN_USERNAME/PASSWORD env vars."

    def handle(self, *args, **options):
        username = os.environ.get("DEMO_ADMIN_USERNAME")
        password = os.environ.get("DEMO_ADMIN_PASSWORD")
        if not username or not password:
            self.stdout.write("DEMO_ADMIN_USERNAME/DEMO_ADMIN_PASSWORD not set — skipping.")
            return

        tenant, _ = Tenant.objects.get_or_create(slug="demo", defaults={"name": "Demo Institute"})

        user, created = User.all_objects.get_or_create(username=username, defaults={"tenant": tenant})
        user.tenant = tenant
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write(f"Demo admin ready (created={created}).")
