from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
import csv
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_number", "full_name", "batch", "tenant", "guardian_phone", "is_active")
    list_filter = ("is_active", "tenant", "batch")
    search_fields = ("roll_number", "user__first_name", "user__last_name", "user__email", "guardian_phone")
    list_select_related = ("user", "batch", "tenant")
    autocomplete_fields = ("user", "batch", "tenant")
    list_per_page = 50
    actions = ["export_as_csv"]

    def get_queryset(self, request):
        qs = Student.all_objects.select_related("user", "batch", "tenant")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Export selected as CSV")
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="students.csv"'
        writer = csv.writer(response)
        writer.writerow(["Roll No", "Name", "Batch", "Guardian Phone", "Active"])
        for s in queryset:
            writer.writerow([s.roll_number, s.full_name(), s.batch, s.guardian_phone, s.is_active])
        return response
