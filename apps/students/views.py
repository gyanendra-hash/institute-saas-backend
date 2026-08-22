from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from common.pagination import StandardResultsPagination
from common.permissions import IsAdminOrReadOnly, IsInstituteAdmin

from .models import Student
from .serializers import StudentSerializer
from .services import bulk_import_students, generate_roll_number


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
        roll_number = serializer.validated_data.get("roll_number") or generate_roll_number(self.request.tenant)
        serializer.save(tenant=self.request.tenant, roll_number=roll_number)

    @action(detail=True, methods=["post"], permission_classes=[IsInstituteAdmin])
    def deactivate(self, request, pk=None):
        """FR-2.1 — deactivate a student profile without deleting their record."""
        student = self.get_object()
        student.is_active = False
        student.save(update_fields=["is_active"])
        return Response(self.get_serializer(student).data)


class StudentBulkImportView(APIView):
    """FR-2.4 — bulk student creation from a CSV upload.

    POST multipart/form-data, field name "file". Columns: username,
    first_name, last_name, email, batch (name, optional), roll_number
    (optional), guardian_name, guardian_phone.
    """

    permission_classes = [IsInstituteAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response(
                {"detail": "No file uploaded — send as multipart form field 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not csv_file.name.lower().endswith(".csv"):
            return Response({"detail": "Only .csv files are supported."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = bulk_import_students(request.tenant, csv_file)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK)
