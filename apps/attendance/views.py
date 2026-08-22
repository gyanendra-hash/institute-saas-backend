from django.db.models import Count, Q
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
        """FR-3.1 — one API call marks attendance for an entire batch on a given date."""
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

    @action(detail=False, methods=["get"])
    def report(self, request):
        """FR-3.3 — attendance % report, per student (?student_id=) or
        aggregated per batch (?batch_id=), optionally bounded by
        ?from=YYYY-MM-DD&to=YYYY-MM-DD.
        """
        student_id = request.query_params.get("student_id")
        batch_id = request.query_params.get("batch_id")
        if not student_id and not batch_id:
            return Response(
                {"detail": "Provide student_id or batch_id."}, status=status.HTTP_400_BAD_REQUEST
            )

        qs = Attendance.objects.all()
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        if student_id:
            summary = qs.filter(student_id=student_id).aggregate(
                total=Count("id"),
                present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
                absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
                leave=Count("id", filter=Q(status=Attendance.Status.LEAVE)),
            )
            percentage = round(summary["present"] / summary["total"] * 100, 2) if summary["total"] else 0.0
            return Response({"student_id": int(student_id), **summary, "attendance_percentage": percentage})

        per_student = (
            qs.filter(student__batch_id=batch_id)
            .values("student_id", "student__roll_number")
            .annotate(
                total=Count("id"),
                present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
            )
            .order_by("student__roll_number")
        )

        rows, total_present, total_records = [], 0, 0
        for row in per_student:
            pct = round(row["present"] / row["total"] * 100, 2) if row["total"] else 0.0
            rows.append(
                {
                    "student_id": row["student_id"],
                    "roll_number": row["student__roll_number"],
                    "total": row["total"],
                    "present": row["present"],
                    "attendance_percentage": pct,
                }
            )
            total_present += row["present"]
            total_records += row["total"]

        batch_average = round(total_present / total_records * 100, 2) if total_records else 0.0
        return Response(
            {"batch_id": int(batch_id), "students": rows, "batch_average_percentage": batch_average}
        )
