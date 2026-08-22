from django.contrib import admin
from .models import Exam, Result


class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    autocomplete_fields = ("student",)
    fields = ("student", "marks_obtained", "remarks")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "batch", "exam_date", "max_marks", "tenant", "result_count")
    list_filter = ("tenant", "batch")
    search_fields = ("title",)
    autocomplete_fields = ("batch", "tenant")
    date_hierarchy = "exam_date"
    inlines = [ResultInline]

    def get_queryset(self, request):
        qs = Exam.all_objects.select_related("batch", "tenant").prefetch_related("results")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)

    @admin.display(description="Results entered")
    def result_count(self, obj):
        return obj.results.count()


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "marks_obtained", "percentage")
    search_fields = ("student__roll_number", "exam__title")
    autocomplete_fields = ("student", "exam")
    list_select_related = ("student", "exam")
