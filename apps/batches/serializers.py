from rest_framework import serializers

from .models import Batch


class BatchSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = Batch
        fields = ["id", "name", "course", "start_date", "end_date", "is_active", "student_count"]
        read_only_fields = ["id", "tenant"]
