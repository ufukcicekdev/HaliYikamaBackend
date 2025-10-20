from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminNotificationViewSet, save_fcm_token, send_test_notification

router = DefaultRouter()
router.register('', AdminNotificationViewSet, basename='admin-notification')

urlpatterns = [
    path('fcm-token/', save_fcm_token, name='save-fcm-token'),
    path('test-notification/', send_test_notification, name='test-notification'),
    path('', include(router.urls)),
]
