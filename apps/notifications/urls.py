from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminNotificationViewSet, UserNotificationViewSet, save_fcm_token, send_test_notification

# Admin notifications router
admin_router = DefaultRouter()
admin_router.register('', AdminNotificationViewSet, basename='admin-notification')

# User notifications router  
user_router = DefaultRouter()
user_router.register('', UserNotificationViewSet, basename='user-notification')

urlpatterns = [
    path('fcm-token/', save_fcm_token, name='save-fcm-token'),
    path('test-notification/', send_test_notification, name='test-notification'),
    path('', include(admin_router.urls)),
]

# User notification URLs (will be included separately)
user_notification_urls = [
    path('', include(user_router.urls)),
]
