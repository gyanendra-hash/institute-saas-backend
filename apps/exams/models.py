from django.db import models
from apps.tenants.models import TenantAwareModel
from apps.tenants.managers import TenantManager
from apps.batches.models import Batch
from apps.students.models import Student


class Exam(TenantAwareModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=255)
    exam_date = models.DateField()
    max_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=35)

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        indexes = [models.Index(fields=["tenant", "batch"])]
        ordering = ["-exam_date"]

    def __str__(self):
        return f"{self.title} — {self.batch}"


class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("exam", "student")
        indexes = [models.Index(fields=["exam", "student"])]

    def __str__(self):
        return f"{self.student.roll_number} — {self.exam.title} — {self.marks_obtained}"

    @property
    def percentage(self):
        return round((self.marks_obtained / self.exam.max_marks) * 100, 2)
