from rest_framework import serializers
from .models import AdminNotification, FCMDevice, UserNotification


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    booking_id = serializers.SerializerMethodField()
    type = serializers.CharField(source='notification_type', read_only=True)
    
    def get_booking_id(self, obj):
        """Return booking ID as string (UUID)."""
        return str(obj.booking.id) if obj.booking else None
    
    class Meta:
        model = AdminNotification
        fields = [
            'id',
            'title',
            'message',
            'type',
            'booking_id',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'type', 'booking_id']


class UserNotificationSerializer(serializers.ModelSerializer):
    booking_id = serializers.SerializerMethodField()
    type = serializers.CharField(source='notification_type', read_only=True)
    
    def get_booking_id(self, obj):
        """Return booking ID as string (UUID)."""
        return str(obj.booking.id) if obj.booking else None
    
    class Meta:
        model = UserNotification
        fields = [
            'id',
            'title',
            'message',
            'type',
            'booking_id',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'type', 'booking_id']
