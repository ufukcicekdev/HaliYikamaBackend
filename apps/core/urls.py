from django.urls import path
from .views import get_notification_sound
from .health import health_check

urlpatterns = [
    path('notification-sound/', get_notification_sound, name='notification-sound'),
    path('health/', health_check, name='health-check'),
]
