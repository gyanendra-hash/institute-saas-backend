from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "student", "student_name", "date", "status", "marked_by"]
        read_only_fields = ["id", "tenant", "marked_by"]

    def validate(self, attrs):
        """FR-3.2 — reject a duplicate student/date instead of letting the
        DB's unique_together raise an unhandled IntegrityError. "tenant" is
        deliberately not a serializer field (it's request-scoped, not
        client-supplied), so DRF's automatic UniqueTogetherValidator can't
        see the (tenant, student, date) constraint — this covers it explicitly.
        """
        student = attrs.get("student", getattr(self.instance, "student", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        qs = Attendance.objects.filter(student=student, date=date)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Attendance already marked for this student on this date.")
        return attrs


class BulkAttendanceEntrySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Attendance.Status.choices)


class BulkAttendanceSerializer(serializers.Serializer):
    """Mark an entire batch's attendance for one date in a single request."""

    batch_id = serializers.IntegerField()
    date = serializers.DateField()
    entries = BulkAttendanceEntrySerializer(many=True)
