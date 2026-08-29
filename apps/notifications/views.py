from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.pagination import StandardResultsPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """FR-6.3 — delivery-status history. Admins/teachers see every
    notification for the tenant; everyone else only sees their own —
    a student/parent has no business reading another student's alerts."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["channel", "status"]

    def get_queryset(self):
        qs = Notification.objects.select_related("user")
        if self.request.user.role in ("admin", "teacher"):
            return qs
        return qs.filter(user=self.request.user)
