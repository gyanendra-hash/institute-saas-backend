from django.contrib import admin

from common.admin import CSVExportMixin

from .models import Student


@admin.register(Student)
class StudentAdmin(CSVExportMixin, admin.ModelAdmin):
    list_display = ("roll_number", "full_name", "batch", "tenant", "guardian_phone", "is_active")
    list_filter = ("is_active", "tenant", "batch")
    search_fields = ("roll_number", "user__first_name", "user__last_name", "user__email", "guardian_phone")
    list_select_related = ("user", "batch", "tenant")
    autocomplete_fields = ("user", "batch", "tenant")
    list_per_page = 50

    def get_queryset(self, request):
        qs = Student.all_objects.select_related("user", "batch", "tenant")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
