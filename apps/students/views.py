from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Student
from .serializers import StudentSerializer
from common.permissions import IsAdminOrReadOnly
from common.pagination import StandardResultsPagination


class StudentViewSet(viewsets.ModelViewSet):
    """Tenant scoping is automatic via Student.objects (TenantManager)."""

    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["batch", "is_active"]
    search_fields = ["roll_number", "user__first_name", "user__last_name"]
    ordering_fields = ["roll_number", "date_of_birth"]

    def get_queryset(self):
        return Student.objects.select_related("user", "batch")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
