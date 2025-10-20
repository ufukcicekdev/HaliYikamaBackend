from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DistrictViewSet,
    CategoryViewSet,
    SubTypeViewSet,
    WorkingHoursViewSet,
    HolidayViewSet,
    BookingSettingsViewSet,
)

router = DefaultRouter()
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subtypes', SubTypeViewSet, basename='subtype')
router.register(r'working-hours', WorkingHoursViewSet, basename='working-hours')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'booking-settings', BookingSettingsViewSet, basename='booking-settings')

urlpatterns = [
    path('', include(router.urls)),
]
