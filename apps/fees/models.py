from django.db import models
from apps.tenants.models import TenantAwareModel
from apps.tenants.managers import TenantManager
from apps.students.models import Student
from apps.batches.models import Batch


class FeeStructure(TenantAwareModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="fee_structures")
    name = models.CharField(max_length=255)  # e.g. "Full Course Fee", "Term 1"
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        indexes = [models.Index(fields=["tenant", "batch"])]
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.name} — {self.batch} — ₹{self.amount}"


class Payment(TenantAwareModel):
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="payments")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "student"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.roll_number} — ₹{self.amount_paid} — {self.status}"
