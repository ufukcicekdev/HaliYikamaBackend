from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookingViewSet,
    TimeSlotViewSet,
)

router = DefaultRouter()
router.register(r'', BookingViewSet, basename='booking')  # Changed from 'bookings' to ''
router.register(r'timeslots', TimeSlotViewSet, basename='timeslot')

urlpatterns = [
    path('', include(router.urls)),
]
