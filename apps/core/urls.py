from django.urls import path
from .views import get_notification_sound

urlpatterns = [
    path('notification-sound/', get_notification_sound, name='notification-sound'),
]
