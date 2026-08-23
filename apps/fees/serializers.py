from rest_framework import serializers
from .models import FeeStructure, Payment


class FeeStructureSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source="batch.name", read_only=True)

    class Meta:
        model = FeeStructure
        fields = ["id", "batch", "batch_name", "name", "amount", "due_date"]
        read_only_fields = ["id"]


class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    fee_structure_name = serializers.CharField(source="fee_structure.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "student", "student_name", "fee_structure", "fee_structure_name",
            "amount_paid", "razorpay_order_id", "razorpay_payment_id", "status",
            "paid_at", "created_at",
        ]
        read_only_fields = [
            "id", "amount_paid", "razorpay_order_id", "razorpay_payment_id",
            "status", "paid_at", "created_at",
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    """FR-4.2 — kicks off a Razorpay order for one fee-structure installment.
    student_id is required when an admin/teacher initiates on a student's
    behalf; a student caller pays for themselves so it's ignored for them.
    """

    fee_structure_id = serializers.IntegerField()
    student_id = serializers.IntegerField(required=False)


class PaymentVerifySerializer(serializers.Serializer):
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
