from rest_framework.routers import DefaultRouter
from .views import FeeStructureViewSet, PaymentViewSet

router = DefaultRouter()
router.register("fees/structures", FeeStructureViewSet, basename="fee-structure")
router.register("fees/payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls
