from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import AdminUserViewSet

router = DefaultRouter()
router.register(r'', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path('', include(router.urls)),
]
