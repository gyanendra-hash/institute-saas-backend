from django.db import models
from apps.tenants.models import TenantAwareModel
from apps.tenants.managers import TenantManager
from apps.students.models import Student


class Attendance(TenantAwareModel):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LEAVE = "leave", "On Leave"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="marked_attendance"
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("tenant", "student", "date")  # prevents duplicate marking
        indexes = [models.Index(fields=["tenant", "student", "date"])]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student.roll_number} — {self.date} — {self.status}"
