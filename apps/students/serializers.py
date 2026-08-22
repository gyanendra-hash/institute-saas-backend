from rest_framework import serializers
from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="user.get_full_name", read_only=True)
    batch_name = serializers.CharField(source="batch.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "user", "student_name", "batch", "batch_name", "roll_number",
            "guardian_name", "guardian_phone", "date_of_birth", "is_active",
        ]
        read_only_fields = ["id", "tenant"]
        extra_kwargs = {
            # System auto-generates it (FR-2.3) when left blank on create.
            "roll_number": {"required": False},
        }
