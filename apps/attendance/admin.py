from django.contrib import admin

from common.admin import CSVExportMixin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(CSVExportMixin, admin.ModelAdmin):
    list_display = ("student", "date", "status", "tenant", "marked_by")
    list_filter = ("status", "tenant", "date")
    search_fields = ("student__roll_number", "student__user__first_name")
    date_hierarchy = "date"
    autocomplete_fields = ("student", "marked_by", "tenant")
    list_select_related = ("student", "tenant", "marked_by")
    list_per_page = 100

    def get_queryset(self, request):
        qs = Attendance.all_objects.select_related("student", "tenant", "marked_by")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)
