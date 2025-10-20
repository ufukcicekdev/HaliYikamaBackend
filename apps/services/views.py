from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import District, Category, SubType, Pricing, WorkingHours, Holiday, BookingSettings
from .serializers import (
    DistrictSerializer,
    CategorySerializer,
    SubTypeSerializer,
    PricingSerializer,
    WorkingHoursSerializer,
    HolidaySerializer,
    BookingSettingsSerializer,
)


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    """Districts where service is available."""
    
    queryset = District.objects.filter(is_active=True)
    serializer_class = DistrictSerializer
    permission_classes = (AllowAny,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name_en', 'name_tr']
    ordering_fields = ['order_priority', 'name_en']
    ordering = ['order_priority']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Get language from request header or query param
        context['language'] = self.request.GET.get('lang', 'en')
        return context


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Service categories."""
    
    queryset = Category.objects.filter(is_active=True).prefetch_related('subtypes__pricing')
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name_en', 'name_tr']
    ordering_fields = ['order_priority', 'name_en']
    ordering = ['order_priority']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.GET.get('lang', 'en')
        return context


class SubTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Service subtypes."""
    
    queryset = SubType.objects.filter(is_active=True).select_related('category').prefetch_related('pricing')
    serializer_class = SubTypeSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'category__slug']
    search_fields = ['name_en', 'name_tr']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.GET.get('lang', 'en')
        return context


class WorkingHoursViewSet(viewsets.ReadOnlyModelViewSet):
    """Working hours configuration."""
    
    queryset = WorkingHours.objects.all()
    serializer_class = WorkingHoursSerializer
    permission_classes = (AllowAny,)
    ordering = ['weekday']


class HolidayViewSet(viewsets.ReadOnlyModelViewSet):
    """Public holidays."""
    
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date']
    ordering = ['date']
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.GET.get('lang', 'en')
        return context


class BookingSettingsViewSet(viewsets.ReadOnlyModelViewSet):
    """Booking settings and rules."""
    
    serializer_class = BookingSettingsSerializer
    permission_classes = (AllowAny,)
    
    def get_queryset(self):
        return BookingSettings.objects.all()
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current booking settings."""
        settings = BookingSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response({
            'success': True,
            'data': serializer.data
        })
