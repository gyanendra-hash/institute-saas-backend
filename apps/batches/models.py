from django.db import models
from apps.tenants.models import TenantAwareModel
from apps.tenants.managers import TenantManager


class Batch(TenantAwareModel):
    name = models.CharField(max_length=255)
    course = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("tenant", "name")
        indexes = [models.Index(fields=["tenant", "is_active"])]
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.course})"
