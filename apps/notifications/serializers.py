from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Read-only — notifications are only ever created by tasks/services,
    never directly by an API client (FR-6.3: delivery-status history)."""

    class Meta:
        model = Notification
        fields = ["id", "user", "channel", "subject", "message", "status", "sent_at", "created_at"]
        read_only_fields = fields
