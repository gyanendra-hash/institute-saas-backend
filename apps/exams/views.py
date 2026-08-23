from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.students.models import Student
from common.pagination import StandardResultsPagination
from common.permissions import IsTeacherOrAdmin

from .models import Exam, Result
from .serializers import BulkMarksEntrySerializer, ExamSerializer


class ExamViewSet(viewsets.ModelViewSet):
    """FR-5.1 — admin/teacher schedules a test/exam for a batch."""

    serializer_class = ExamSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["batch"]

    def get_queryset(self):
        return Exam.objects.select_related("batch")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

    @action(detail=True, methods=["post"], url_path="enter-marks")
    def enter_marks(self, request, pk=None):
        """FR-5.2 — enter/update marks for many students against this exam
        in one call. Rejects the whole request (with a per-row detail) if
        any entry names a student outside this exam's tenant or exceeds
        max_marks, instead of silently skipping or clamping bad rows."""
        exam = self.get_object()
        serializer = BulkMarksEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entries = serializer.validated_data["entries"]

        student_ids = [entry["student_id"] for entry in entries]
        students = set(Student.objects.filter(id__in=student_ids).values_list("id", flat=True))

        errors = []
        for entry in entries:
            if entry["student_id"] not in students:
                errors.append({"student_id": entry["student_id"], "error": "Student not found."})
            elif entry["marks_obtained"] > exam.max_marks:
                errors.append(
                    {
                        "student_id": entry["student_id"],
                        "error": f"marks_obtained exceeds max_marks ({exam.max_marks}).",
                    }
                )
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        created, updated = 0, 0
        for entry in entries:
            obj, was_created = Result.objects.update_or_create(
                exam=exam,
                student_id=entry["student_id"],
                defaults={"marks_obtained": entry["marks_obtained"], "remarks": entry.get("remarks", "")},
            )
            created += was_created
            updated += not was_created

        return Response({"exam_id": exam.id, "created": created, "updated": updated})

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        """FR-5.3 — rank, average, and pass/fail status for every student
        with a recorded result for this exam. Competition ranking: tied
        marks share a rank, and the next rank skips ahead accordingly."""
        exam = self.get_object()
        results = exam.results.select_related("student__user").order_by("-marks_obtained")

        rows = []
        rank = 0
        prev_marks = None
        pass_count = fail_count = 0
        total_marks = Decimal("0")
        for i, result in enumerate(results, start=1):
            if result.marks_obtained != prev_marks:
                rank = i
                prev_marks = result.marks_obtained
            passed = result.marks_obtained >= exam.passing_marks
            pass_count += int(passed)
            fail_count += int(not passed)
            total_marks += result.marks_obtained
            rows.append(
                {
                    "student_id": result.student_id,
                    "roll_number": result.student.roll_number,
                    "student_name": result.student.user.get_full_name() or result.student.user.username,
                    "marks_obtained": result.marks_obtained,
                    "percentage": result.percentage,
                    "rank": rank,
                    "status": "pass" if passed else "fail",
                }
            )

        count = len(rows)
        average_marks = round(total_marks / count, 2) if count else Decimal("0")
        average_percentage = round(float(average_marks) / exam.max_marks * 100, 2) if count else 0.0

        return Response(
            {
                "exam_id": exam.id,
                "title": exam.title,
                "max_marks": exam.max_marks,
                "passing_marks": exam.passing_marks,
                "average_marks": average_marks,
                "average_percentage": average_percentage,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "results": rows,
            }
        )

    @action(detail=False, methods=["get"], url_path="my-results", permission_classes=[IsAuthenticated])
    def my_results(self, request):
        """FR-5.4 — a student's own results and performance trend across
        exams; admin/teacher can look up another student's via
        ?student_id= for oversight. There's no Parent->Student link
        anywhere in the schema yet (Student only stores free-text
        guardian_name/guardian_phone), so a parent-role caller is refused
        rather than allowed to pull up any student by guessing an id —
        see README known gaps."""
        if request.user.role == "student":
            student = get_object_or_404(Student.objects.all(), user=request.user)
        elif request.user.role in ("admin", "teacher"):
            student_id = request.query_params.get("student_id")
            if not student_id:
                return Response(
                    {"detail": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST
                )
            student = get_object_or_404(Student.objects.all(), id=student_id)
        else:
            return Response(
                {"detail": "Parent-student linking isn't implemented yet."},
                status=status.HTTP_403_FORBIDDEN,
            )

        results = (
            Result.objects.filter(student=student)
            .select_related("exam", "exam__batch")
            .order_by("exam__exam_date")
        )
        rows = [
            {
                "exam_id": result.exam_id,
                "title": result.exam.title,
                "exam_date": result.exam.exam_date,
                "batch_name": result.exam.batch.name,
                "marks_obtained": result.marks_obtained,
                "max_marks": result.exam.max_marks,
                "percentage": result.percentage,
                "status": "pass" if result.marks_obtained >= result.exam.passing_marks else "fail",
            }
            for result in results
        ]
        average_percentage = round(sum(row["percentage"] for row in rows) / len(rows), 2) if rows else 0.0

        return Response(
            {
                "student_id": student.id,
                "roll_number": student.roll_number,
                "results": rows,
                "average_percentage": average_percentage,
            }
        )
