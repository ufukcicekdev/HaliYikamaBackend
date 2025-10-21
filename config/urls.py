from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from apps.notifications.urls import user_notification_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/auth/', include('apps.accounts.urls')),
    
    # Services
    path('api/services/', include('apps.services.urls')),
    
    # Customer endpoints
    path('api/customer/bookings/', include('apps.bookings.urls')),
    path('api/customer/notifications/', include(user_notification_urls)),
    
    # Admin endpoints
    path('api/admin/', include('apps.bookings.admin_urls')),
    path('api/admin/notifications/', include('apps.notifications.urls')),
    
    # Payments
    path('api/payments/', include('apps.payments.urls')),
    
    # Core
    path('api/core/', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
