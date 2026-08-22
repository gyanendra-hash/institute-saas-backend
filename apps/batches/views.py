from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.students.models import Student
from common.pagination import StandardResultsPagination
from common.permissions import IsAdminOrReadOnly, IsInstituteAdmin

from .models import Batch
from .serializers import BatchSerializer


class BatchViewSet(viewsets.ModelViewSet):
    """Tenant scoping is automatic via Batch.objects (TenantManager)."""

    serializer_class = BatchSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["course", "is_active"]
    search_fields = ["name", "course"]
    ordering_fields = ["start_date", "name"]

    def get_queryset(self):
        return Batch.objects.prefetch_related("students")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

    @action(detail=True, methods=["post"], permission_classes=[IsInstituteAdmin])
    def assign_students(self, request, pk=None):
        """FR-2.2 — assign a list of existing students to this batch in one call."""
        batch = self.get_object()
        student_ids = request.data.get("student_ids", [])
        if not isinstance(student_ids, list) or not student_ids:
            return Response({"detail": "student_ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        updated = Student.objects.filter(tenant=request.tenant, id__in=student_ids).update(batch=batch)
        return Response({"assigned": updated, "batch": batch.id})
