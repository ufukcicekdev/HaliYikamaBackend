from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, PaymentViewSet, WebhookView

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'payment', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:gateway>/', WebhookView.as_view(), name='payment_webhook'),
]
