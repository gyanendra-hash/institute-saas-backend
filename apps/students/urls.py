from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import StudentBulkImportView, StudentViewSet

router = DefaultRouter()
router.register("students", StudentViewSet, basename="student")

urlpatterns = [
    # Must precede router.urls — otherwise "bulk-import" matches the
    # router's students/<pk>/ detail pattern first and 404s.
    path("students/bulk-import/", StudentBulkImportView.as_view(), name="student-bulk-import"),
] + router.urls
