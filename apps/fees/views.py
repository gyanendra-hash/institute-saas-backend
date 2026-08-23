from decimal import Decimal

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from razorpay.errors import SignatureVerificationError

from apps.students.models import Student
from common.pagination import StandardResultsPagination
from common.permissions import IsAdminOrReadOnly, IsInstituteAdmin, IsTeacherOrAdmin

from .models import FeeStructure, Payment
from .serializers import (
    FeeStructureSerializer,
    PaymentInitiateSerializer,
    PaymentSerializer,
    PaymentVerifySerializer,
)
from .services.payment_gateway import RazorpayService


class FeeStructureViewSet(viewsets.ModelViewSet):
    """FR-4.1 — fee structures per batch/course. An installment plan is
    modeled as several rows sharing a batch (e.g. "Term 1", "Term 2")."""

    serializer_class = FeeStructureSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["batch"]

    def get_queryset(self):
        return FeeStructure.objects.select_related("batch")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


class PaymentViewSet(viewsets.ModelViewSet):
    """Admin/teacher can list, filter, and reconcile payments. Paying is
    done through the initiate/verify actions below, open to any
    authenticated tenant user so a student can settle their own dues."""

    serializer_class = PaymentSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["student", "fee_structure", "status"]

    def get_queryset(self):
        return Payment.objects.select_related("student__user", "fee_structure__batch")

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def initiate(self, request):
        """FR-4.2 — creates a pending Payment and a matching Razorpay order
        for one fee-structure installment."""
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        fee_structure = get_object_or_404(FeeStructure.objects.all(), id=data["fee_structure_id"])

        if request.user.role == "student":
            student = get_object_or_404(Student.objects.all(), user=request.user)
        else:
            student_id = data.get("student_id")
            if not student_id:
                return Response(
                    {"detail": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST
                )
            student = get_object_or_404(Student.objects.all(), id=student_id)

        payment = Payment.objects.create(
            tenant=request.tenant,
            student=student,
            fee_structure=fee_structure,
            amount_paid=fee_structure.amount,
        )
        order = RazorpayService().create_order(payment)

        return Response(
            {
                "payment_id": payment.id,
                "razorpay_order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def verify(self, request, pk=None):
        """FR-4.2 — verifies the Razorpay signature from the client callback
        and marks the payment successful; that in turn queues the async PDF
        receipt (FR-4.3) from RazorpayService.verify_and_mark_paid."""
        payment = self.get_object()

        if request.user.role == "student" and payment.student.user_id != request.user.id:
            return Response({"detail": "Not your payment."}, status=status.HTTP_403_FORBIDDEN)

        if payment.status == Payment.PaymentStatus.SUCCESS:
            return Response(
                {"detail": "Payment already verified."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            RazorpayService().verify_and_mark_paid(
                payment,
                serializer.validated_data["razorpay_payment_id"],
                serializer.validated_data["razorpay_signature"],
            )
        except SignatureVerificationError:
            payment.status = Payment.PaymentStatus.FAILED
            payment.save(update_fields=["status"])
            return Response(
                {"detail": "Signature verification failed."}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(PaymentSerializer(payment).data)

    @action(detail=False, methods=["get"], permission_classes=[IsInstituteAdmin])
    def outstanding(self, request):
        """FR-4.5 — outstanding dues across all students, optionally scoped
        to one batch via ?batch_id=."""
        batch_id = request.query_params.get("batch_id")
        fee_structures = FeeStructure.objects.select_related("batch")
        if batch_id:
            fee_structures = fee_structures.filter(batch_id=batch_id)

        rows = []
        total_outstanding = Decimal("0")
        for fs in fee_structures:
            paid_student_ids = Payment.objects.filter(
                fee_structure=fs, status=Payment.PaymentStatus.SUCCESS
            ).values_list("student_id", flat=True)
            unpaid = (
                fs.batch.students.filter(is_active=True)
                .exclude(id__in=paid_student_ids)
                .select_related("user")
            )
            for student in unpaid:
                rows.append(
                    {
                        "student_id": student.id,
                        "roll_number": student.roll_number,
                        "student_name": student.user.get_full_name() or student.user.username,
                        "fee_structure_id": fs.id,
                        "fee_structure_name": fs.name,
                        "batch_id": fs.batch_id,
                        "batch_name": fs.batch.name,
                        "amount_due": fs.amount,
                        "due_date": fs.due_date,
                    }
                )
                total_outstanding += fs.amount

        return Response(
            {"outstanding": rows, "count": len(rows), "total_outstanding": total_outstanding}
        )
