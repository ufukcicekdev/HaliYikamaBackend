from django.urls import path
from .views import (
    BookingViewSet,
    admin_customers,
    admin_customer_detail,
    admin_reports,
    admin_settings,
    admin_stats,
    admin_recent_bookings,
)

urlpatterns = [
    path('bookings/', BookingViewSet.as_view({'get': 'list'}), name='admin-bookings'),
    path('bookings/<uuid:pk>/', BookingViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'put': 'update', 'delete': 'destroy'}), name='admin-booking-detail'),
    path('customers/', admin_customers, name='admin-customers'),
    path('customers/<int:customer_id>/', admin_customer_detail, name='admin-customer-detail'),
    path('reports/', admin_reports, name='admin-reports'),
    path('settings/', admin_settings, name='admin-settings'),
    path('stats/', admin_stats, name='admin-stats'),
    path('recent-bookings/', admin_recent_bookings, name='admin-recent-bookings'),
]
