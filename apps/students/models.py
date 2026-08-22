from django.db import models
from apps.tenants.models import TenantAwareModel
from apps.tenants.managers import TenantManager
from apps.accounts.models import User
from apps.batches.models import Batch


class Student(TenantAwareModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    roll_number = models.CharField(max_length=50)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("tenant", "roll_number")
        indexes = [models.Index(fields=["tenant", "batch"])]
        ordering = ["roll_number"]

    def __str__(self):
        return f"{self.roll_number} — {self.user.get_full_name() or self.user.username}"
