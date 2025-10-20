from rest_framework import serializers
from decimal import Decimal
from .models import Booking, BookingItem, TimeSlot, BookingStatusHistory
from apps.accounts.serializers import AddressSerializer
from apps.services.serializers import SubTypeSerializer


class BookingItemSerializer(serializers.ModelSerializer):
    """Booking item serializer."""
    
    subtype_details = SubTypeSerializer(source='subtype', read_only=True)
    
    class Meta:
        model = BookingItem
        fields = (
            'id', 'subtype', 'subtype_details', 'quantity',
            'unit_price', 'line_total', 'notes'
        )
        read_only_fields = ('line_total',)


class BookingItemCreateSerializer(serializers.Serializer):
    """Nested serializer for creating booking items."""
    
    subtype_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    notes = serializers.CharField(required=False, allow_blank=True)


class BookingListSerializer(serializers.ModelSerializer):
    """Booking list serializer (simplified)."""
    
    pickup_address_details = AddressSerializer(source='pickup_address', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = (
            'id', 'booking_number', 'status', 'status_display',
            'pickup_date', 'pickup_address_details',
            'total', 'currency', 'created_at'
        )


class BookingDetailSerializer(serializers.ModelSerializer):
    """Booking detail serializer (full)."""
    
    items = BookingItemSerializer(many=True, read_only=True)
    pickup_address_details = AddressSerializer(source='pickup_address', read_only=True)
    delivery_address_details = AddressSerializer(source='delivery_address', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_technician_name = serializers.CharField(
        source='assigned_technician.get_full_name',
        read_only=True,
        allow_null=True
    )
    can_cancel = serializers.SerializerMethodField()
    can_reschedule = serializers.SerializerMethodField()
    cancellation_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = (
            'id', 'booking_number', 'user', 'status', 'status_display',
            'pickup_address', 'pickup_address_details',
            'delivery_address', 'delivery_address_details',
            'pickup_date', 'pickup_time_slot', 'delivery_date', 'delivery_time_slot',
            'assigned_technician', 'assigned_technician_name',
            'subtotal', 'delivery_fee', 'discount', 'total', 'currency',
            'customer_notes', 'admin_notes', 'cancellation_reason',
            'items', 'created_at', 'updated_at',
            'confirmed_at', 'completed_at', 'cancelled_at',
            'can_cancel', 'can_reschedule', 'cancellation_info'
        )
        read_only_fields = (
            'id', 'booking_number', 'user', 'total',
            'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'
        )
    
    def get_can_cancel(self, obj):
        can_cancel, _ = obj.can_cancel()
        return can_cancel
    
    def get_can_reschedule(self, obj):
        can_reschedule, _ = obj.can_reschedule()
        return can_reschedule
    
    def get_cancellation_info(self, obj):
        from apps.services.models import BookingSettings
        settings = BookingSettings.get_settings()
        can_cancel, message = obj.can_cancel()
        
        return {
            'can_cancel': can_cancel,
            'message': message,
            'min_notice_hours': settings.min_cancellation_notice_hours,
            'cancellation_fee_percentage': float(settings.cancellation_fee_percentage)
        }


class BookingCreateSerializer(serializers.ModelSerializer):
    """Booking creation serializer."""
    
    items = BookingItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Booking
        fields = (
            'pickup_address', 'delivery_address', 'pickup_date', 'pickup_time_slot',
            'delivery_date', 'delivery_time_slot', 'customer_notes', 'items'
        )
    
    def validate(self, attrs):
        # Validate time slot availability
        pickup_slot = attrs.get('pickup_time_slot')
        if not pickup_slot.is_slot_available():
            raise serializers.ValidationError({
                'pickup_time_slot': 'This time slot is no longer available.'
            })
        
        # Validate items
        items_data = attrs.get('items', [])
        if not items_data:
            raise serializers.ValidationError({
                'items': 'At least one item is required.'
            })
        
        return attrs
    
    def create(self, validated_data):
        from apps.services.models import SubType
        
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        
        # Calculate pricing
        subtotal = Decimal('0.00')
        for item_data in items_data:
            subtype = SubType.objects.get(id=item_data['subtype_id'])
            current_pricing = subtype.pricing.filter(is_active=True).first()
            if not current_pricing:
                raise serializers.ValidationError({
                    'items': f'No active pricing for {subtype.name_en}'
                })
            
            unit_price = current_pricing.get_final_price()
            quantity = item_data['quantity']
            subtotal += unit_price * quantity
        
        # Get delivery fee from district
        delivery_fee = validated_data['pickup_address'].district.delivery_fee
        
        # Create booking
        booking = Booking.objects.create(
            user=user,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            **validated_data
        )
        
        # Create booking items
        for item_data in items_data:
            subtype = SubType.objects.get(id=item_data['subtype_id'])
            current_pricing = subtype.pricing.filter(is_active=True).first()
            
            BookingItem.objects.create(
                booking=booking,
                subtype=subtype,
                quantity=item_data['quantity'],
                unit_price=current_pricing.get_final_price(),
                notes=item_data.get('notes', '')
            )
        
        # Increment slot booking count
        booking.pickup_time_slot.increment_bookings()
        if booking.delivery_time_slot:
            booking.delivery_time_slot.increment_bookings()
        
        return booking


class TimeSlotSerializer(serializers.ModelSerializer):
    """Time slot serializer."""
    
    is_available_now = serializers.BooleanField(source='is_slot_available', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = (
            'id', 'date', 'start_time', 'end_time',
            'max_capacity', 'current_bookings', 'is_available', 'is_available_now'
        )


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Update booking status."""
    
    status = serializers.ChoiceField(choices=Booking.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    """Booking status history serializer."""
    
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = BookingStatusHistory
        fields = ('id', 'old_status', 'new_status', 'changed_by', 'changed_by_name', 'notes', 'created_at')
