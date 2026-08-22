from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "plan", "is_active", "contact_email", "created_at")
    list_filter = ("plan", "is_active")
    search_fields = ("name", "slug", "domain", "contact_email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50
    fieldsets = (
        ("Institute Info", {"fields": ("name", "slug", "domain", "is_active", "plan")}),
        ("Contact", {"fields": ("contact_email", "contact_phone")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
