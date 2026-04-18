from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import TransactionAdminViewSet, RefundAdminViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionAdminViewSet, basename='admin-transaction')
router.register(r'refunds', RefundAdminViewSet, basename='admin-refund')

urlpatterns = [
    path('', include(router.urls)),
]
