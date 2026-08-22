from django.contrib import admin
from .models import Batch


class StudentInline(admin.TabularInline):
    from apps.students.models import Student
    model = Student
    fields = ("roll_number", "user", "is_active")
    extra = 0
    show_change_link = True
    autocomplete_fields = ("user",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "tenant", "start_date", "end_date", "is_active", "student_count")
    list_filter = ("is_active", "tenant", "course")
    search_fields = ("name", "course")
    list_select_related = ("tenant",)
    autocomplete_fields = ("tenant",)
    date_hierarchy = "start_date"
    list_per_page = 50
    inlines = [StudentInline]

    def get_queryset(self, request):
        qs = Batch.all_objects.select_related("tenant").prefetch_related("students")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)

    @admin.display(description="Students")
    def student_count(self, obj):
        return obj.students.count()
