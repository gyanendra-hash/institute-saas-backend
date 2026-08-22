from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Attendance
from .serializers import AttendanceSerializer, BulkAttendanceSerializer
from common.permissions import IsTeacherOrAdmin
from common.pagination import StandardResultsPagination


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["student", "date", "status"]

    def get_queryset(self):
        return Attendance.objects.select_related("student", "student__user")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, marked_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="bulk-mark")
    def bulk_mark(self, request):
        """One API call marks attendance for an entire batch on a given date."""
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        created, updated = 0, 0
        for entry in data["entries"]:
            obj, was_created = Attendance.objects.update_or_create(
                tenant=request.tenant,
                student_id=entry["student_id"],
                date=data["date"],
                defaults={"status": entry["status"], "marked_by": request.user},
            )
            created += was_created
            updated += not was_created

        return Response(
            {"batch_id": data["batch_id"], "date": data["date"], "created": created, "updated": updated},
            status=status.HTTP_200_OK,
        )
