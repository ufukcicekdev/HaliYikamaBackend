from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import serializers as drf_serializers
from django_filters.rest_framework import DjangoFilterBackend
from .models import District, Category, SubType, Pricing, WorkingHours, Holiday, BookingSettings
from .serializers import (
    WorkingHoursSerializer,
    HolidaySerializer,
    BookingSettingsSerializer,
)


# Admin-specific serializers with all writable fields

class AdminDistrictSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class AdminCategorySerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class AdminSubTypeSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = SubType
        fields = '__all__'


class AdminPricingSerializer(drf_serializers.ModelSerializer):
    final_price = drf_serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source='get_final_price'
    )

    class Meta:
        model = Pricing
        fields = '__all__'


class AdminWorkingHoursSerializer(drf_serializers.ModelSerializer):
    weekday_display = drf_serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = WorkingHours
        fields = '__all__'


class AdminHolidaySerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'


class AdminBookingSettingsSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = BookingSettings
        fields = '__all__'


# Admin ViewSets

class DistrictAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for Districts."""
    queryset = District.objects.all()
    serializer_class = AdminDistrictSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['order_priority', 'name', 'created_at']
    ordering = ['order_priority']


class CategoryAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for Categories."""
    queryset = Category.objects.all().prefetch_related('subtypes')
    serializer_class = AdminCategorySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'slug', 'description']
    filterset_fields = ['is_active', 'pricing_type']
    ordering_fields = ['order_priority', 'name', 'created_at']
    ordering = ['order_priority']


class SubTypeAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for SubTypes."""
    queryset = SubType.objects.all().select_related('category').prefetch_related('pricing')
    serializer_class = AdminSubTypeSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['order_priority', 'name', 'created_at']
    ordering = ['order_priority']


class PricingAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for Pricing."""
    queryset = Pricing.objects.all().select_related('subtype__category')
    serializer_class = AdminPricingSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['subtype', 'is_active', 'currency']
    ordering_fields = ['created_at', 'base_price']
    ordering = ['-created_at']


class WorkingHoursAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for WorkingHours."""
    queryset = WorkingHours.objects.all()
    serializer_class = AdminWorkingHoursSerializer
    permission_classes = [IsAdminUser]
    ordering = ['weekday']


class HolidayAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for Holidays."""
    queryset = Holiday.objects.all()
    serializer_class = AdminHolidaySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date']
    ordering = ['date']


class BookingSettingsAdminViewSet(viewsets.ModelViewSet):
    """Admin CRUD for BookingSettings (singleton)."""
    queryset = BookingSettings.objects.all()
    serializer_class = AdminBookingSettingsSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get or create the singleton BookingSettings."""
        settings = BookingSettings.get_settings()
        serializer = self.get_serializer(settings)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['put', 'patch'])
    def update_current(self, request):
        """Update the singleton BookingSettings."""
        settings = BookingSettings.get_settings()
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(settings, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'data': serializer.data})
