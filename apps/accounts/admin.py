from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("username", "email", "role", "tenant", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "tenant")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    list_select_related = ("tenant",)
    autocomplete_fields = ("tenant",)
    list_per_page = 50

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Institute Info", {"fields": ("tenant", "role", "phone")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Institute Info", {"fields": ("tenant", "role", "phone")}),
    )

    def get_queryset(self, request):
        # Platform superusers see everyone; staff scoped to own tenant only.
        qs = User.all_objects.all()
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)
