from rest_framework import serializers
from .models import Exam, Result


class ExamSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source="batch.name", read_only=True)

    class Meta:
        model = Exam
        fields = ["id", "batch", "batch_name", "title", "exam_date", "max_marks", "passing_marks"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        max_marks = attrs.get("max_marks", getattr(self.instance, "max_marks", None))
        passing_marks = attrs.get("passing_marks", getattr(self.instance, "passing_marks", None))
        if max_marks is not None and passing_marks is not None and passing_marks > max_marks:
            raise serializers.ValidationError("passing_marks cannot exceed max_marks.")
        return attrs


class ResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Result
        fields = ["id", "exam", "student", "student_name", "marks_obtained", "remarks", "percentage"]
        read_only_fields = ["id", "percentage"]


class MarkEntrySerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    marks_obtained = serializers.DecimalField(max_digits=6, decimal_places=2)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class BulkMarksEntrySerializer(serializers.Serializer):
    """FR-5.2 — enter marks for many students against one exam in one call."""

    entries = MarkEntrySerializer(many=True)
