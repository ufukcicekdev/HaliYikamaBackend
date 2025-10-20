from rest_framework import serializers
from .models import District, Category, SubType, Pricing, WorkingHours, Holiday, BookingSettings


class DistrictSerializer(serializers.ModelSerializer):
    """District serializer."""
    
    class Meta:
        model = District
        fields = ('id', 'name', 'delivery_fee', 'is_active', 'order_priority')


class PricingSerializer(serializers.ModelSerializer):
    """Pricing serializer."""
    
    final_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        source='get_final_price'
    )
    
    class Meta:
        model = Pricing
        fields = (
            'id', 'base_price', 'final_price', 'currency',
            'discount_percentage', 'valid_from', 'valid_until', 'is_active'
        )


class SubTypeSerializer(serializers.ModelSerializer):
    """SubType serializer."""
    
    pricing = PricingSerializer(many=True, read_only=True)
    current_price = serializers.SerializerMethodField()
    
    class Meta:
        model = SubType
        fields = (
            'id', 'name', 'slug', 'description', 'icon', 'image',
            'is_active', 'pricing', 'current_price'
        )
    
    def get_current_price(self, obj):
        """Get currently active pricing."""
        from django.utils import timezone
        active_pricing = obj.pricing.filter(
            is_active=True,
        ).first()
        
        if active_pricing:
            return PricingSerializer(active_pricing).data
        return None


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer."""
    
    subtypes = SubTypeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description',
            'icon', 'image', 'pricing_type', 'is_active', 'subtypes',
            'requires_time_selection', 'requires_pickup_delivery', 'min_days_between_pickup_delivery'
        )


class WorkingHoursSerializer(serializers.ModelSerializer):
    """Working hours serializer."""
    
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = WorkingHours
        fields = (
            'id', 'weekday', 'weekday_display', 'is_working_day',
            'opening_time', 'closing_time', 'slot_duration_minutes',
            'max_bookings_per_slot'
        )


class HolidaySerializer(serializers.ModelSerializer):
    """Holiday serializer."""
    
    class Meta:
        model = Holiday
        fields = ('id', 'date', 'name')


class BookingSettingsSerializer(serializers.ModelSerializer):
    """Booking settings serializer."""
    
    class Meta:
        model = BookingSettings
        fields = (
            'min_cancellation_notice_hours',
            'min_reschedule_notice_hours',
            'cancellation_fee_percentage',
            'late_cancellation_fee_percentage',
            'default_service_start_time',
            'default_service_end_time'
        )
