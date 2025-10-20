from rest_framework import serializers
from .models import AdminNotification, FCMDevice


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='booking.id', read_only=True, allow_null=True)
    type = serializers.CharField(source='notification_type', read_only=True)
    
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
