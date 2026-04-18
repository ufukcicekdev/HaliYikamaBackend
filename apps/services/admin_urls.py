from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import (
    DistrictAdminViewSet,
    CategoryAdminViewSet,
    SubTypeAdminViewSet,
    PricingAdminViewSet,
    WorkingHoursAdminViewSet,
    HolidayAdminViewSet,
    BookingSettingsAdminViewSet,
)

router = DefaultRouter()
router.register(r'districts', DistrictAdminViewSet, basename='admin-district')
router.register(r'categories', CategoryAdminViewSet, basename='admin-category')
router.register(r'subtypes', SubTypeAdminViewSet, basename='admin-subtype')
router.register(r'pricing', PricingAdminViewSet, basename='admin-pricing')
router.register(r'working-hours', WorkingHoursAdminViewSet, basename='admin-working-hours')
router.register(r'holidays', HolidayAdminViewSet, basename='admin-holiday')
router.register(r'booking-settings', BookingSettingsAdminViewSet, basename='admin-booking-settings')

urlpatterns = [
    path('', include(router.urls)),
]
