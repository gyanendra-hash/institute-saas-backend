from django.contrib import admin
from django.db.models import Sum

from common.admin import CSVExportMixin

from .models import FeeStructure, Payment


@admin.register(FeeStructure)
class FeeStructureAdmin(CSVExportMixin, admin.ModelAdmin):
    list_display = ("name", "batch", "amount", "due_date", "tenant")
    list_filter = ("tenant", "due_date")
    search_fields = ("name", "batch__name")
    autocomplete_fields = ("batch", "tenant")
    list_select_related = ("batch", "tenant")

    def get_queryset(self, request):
        qs = FeeStructure.all_objects.select_related("batch", "tenant")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)


@admin.register(Payment)
class PaymentAdmin(CSVExportMixin, admin.ModelAdmin):
    list_display = ("student", "fee_structure", "amount_paid", "status", "paid_at", "tenant")
    list_filter = ("status", "tenant")
    search_fields = ("student__roll_number", "razorpay_payment_id", "razorpay_order_id")
    readonly_fields = ("razorpay_order_id", "razorpay_payment_id", "created_at")
    autocomplete_fields = ("student", "fee_structure", "tenant")
    list_select_related = ("student", "fee_structure", "tenant")
    date_hierarchy = "created_at"
    list_per_page = 50

    def get_queryset(self, request):
        qs = Payment.all_objects.select_related("student", "fee_structure", "tenant")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)

    def changelist_view(self, request, extra_context=None):
        # quick revenue summary shown above the list — collected total for successful payments
        qs = self.get_queryset(request).filter(status=Payment.PaymentStatus.SUCCESS)
        total_collected = qs.aggregate(total=Sum("amount_paid"))["total"] or 0
        extra_context = extra_context or {}
        extra_context["total_collected"] = total_collected
        return super().changelist_view(request, extra_context=extra_context)
