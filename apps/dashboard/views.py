from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance.models import Attendance
from apps.fees.models import FeeStructure, Payment
from apps.students.models import Student
from common.permissions import IsTeacherOrAdmin


class DashboardSummaryView(APIView):
    """FR-7.3 — headline numbers for the admin/teacher dashboard: revenue
    collected, active students, outstanding dues, and attendance % over a
    trailing window (default 30 days, override with ?days=)."""

    permission_classes = [IsTeacherOrAdmin]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            days = 30
        since = timezone.now().date() - timedelta(days=days)

        active_students = Student.objects.filter(is_active=True).count()

        revenue_collected = Payment.objects.filter(
            status=Payment.PaymentStatus.SUCCESS
        ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")

        # Same per-fee-structure unpaid-count approach as
        # PaymentViewSet.outstanding (apps/fees/views.py) — kept consistent
        # rather than reimplementing the dues calculation differently here.
        outstanding_dues = Decimal("0")
        for fee_structure in FeeStructure.objects.select_related("batch"):
            paid_student_ids = Payment.objects.filter(
                fee_structure=fee_structure, status=Payment.PaymentStatus.SUCCESS
            ).values_list("student_id", flat=True)
            unpaid_count = (
                fee_structure.batch.students.filter(is_active=True)
                .exclude(id__in=paid_student_ids)
                .count()
            )
            outstanding_dues += fee_structure.amount * unpaid_count

        attendance_counts = Attendance.objects.filter(date__gte=since).aggregate(
            total=Count("id"),
            present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
        )
        total_marked = attendance_counts["total"] or 0
        attendance_percentage = (
            round((attendance_counts["present"] / total_marked) * 100, 2) if total_marked else None
        )

        return Response(
            {
                "active_students": active_students,
                "revenue_collected": revenue_collected,
                "outstanding_dues": outstanding_dues,
                "attendance_percentage": attendance_percentage,
                "attendance_window_days": days,
            }
        )
