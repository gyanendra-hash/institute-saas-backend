from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    """Each coaching institute is one Tenant. Shared-DB + tenant_id isolation."""

    PLAN_CHOICES = [("free", "Free"), ("basic", "Basic"), ("pro", "Pro")]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)  # subdomain: abc.yoursaas.com
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")

    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TenantAwareModel(models.Model):
    """Abstract base — every tenant-scoped model inherits this for tenant_id + index."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="%(class)ss")

    class Meta:
        abstract = True
        indexes = [models.Index(fields=["tenant"])]
