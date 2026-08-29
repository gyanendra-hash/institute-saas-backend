from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "channel", "subject", "status", "sent_at", "tenant")
    list_filter = ("channel", "status", "tenant")
    search_fields = ("user__username", "user__email", "subject")
    autocomplete_fields = ("user", "tenant")
    list_select_related = ("user", "tenant")
    readonly_fields = ("sent_at", "created_at")
    date_hierarchy = "created_at"
    list_per_page = 50

    def get_queryset(self, request):
        qs = Notification.all_objects.select_related("user", "tenant")
        if request.user.is_superuser:
            return qs
        return qs.filter(tenant=request.user.tenant)
