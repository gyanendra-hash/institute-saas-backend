from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from apps.tenants.models import Tenant
from apps.tenants.managers import TenantManager


class TenantUserManager(UserManager, TenantManager):
    """UserManager (create_user/create_superuser — needed by `createsuperuser`
    and bulk student import) combined with TenantManager (tenant-scoped
    querysets for list/detail views)."""


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        ADMIN = "admin", "Institute Admin"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"
        PARENT = "parent", "Parent"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users", null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)

    objects = TenantUserManager()      # tenant-scoped by default, has create_user/create_superuser
    all_objects = UserManager()        # unscoped — auth backend / superadmin / bulk import use

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "role"]),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_institute_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER
