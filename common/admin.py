import csv

from django.contrib import admin
from django.http import HttpResponse


class CSVExportMixin:
    """FR-7.4 — generic 'export selected as CSV' admin action. Reuses each
    ModelAdmin's own list_display as the column set, so every admin gets an
    export button for free instead of hand-rolling one per model."""

    actions = ["export_as_csv"]

    @admin.display(description="Export selected as CSV")
    def export_as_csv(self, request, queryset):
        field_names = [f for f in self.list_display if f != "export_as_csv"]

        response = HttpResponse(content_type="text/csv")
        model_name = queryset.model._meta.model_name
        response["Content-Disposition"] = f'attachment; filename="{model_name}.csv"'

        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = []
            for field in field_names:
                admin_attr = getattr(self, field, None)
                if callable(admin_attr):
                    value = admin_attr(obj)
                else:
                    value = getattr(obj, field, "")
                    if callable(value):
                        value = value()
                row.append(value)
            writer.writerow(row)
        return response
