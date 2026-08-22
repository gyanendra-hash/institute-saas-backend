from django.db import models
from apps.tenants.models import TenantAwareModel
from apps.tenants.managers import TenantManager


class Notification(TenantAwareModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        indexes = [models.Index(fields=["tenant", "status"])]
        ordering = ["-created_at"]
