from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "student", "student_name", "date", "status", "marked_by"]
        read_only_fields = ["id", "tenant", "marked_by"]


class BulkAttendanceEntrySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Attendance.Status.choices)


class BulkAttendanceSerializer(serializers.Serializer):
    """Mark an entire batch's attendance for one date in a single request."""

    batch_id = serializers.IntegerField()
    date = serializers.DateField()
    entries = BulkAttendanceEntrySerializer(many=True)
