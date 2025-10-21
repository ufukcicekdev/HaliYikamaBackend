from django.contrib import admin
from django.contrib import messages
from .models import Notification, NotificationPreference, AdminNotification, FCMDevice, UserNotification
from .fcm_service import FCMService


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'booking', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('İlişkili Bilgiler', {
            'fields': ('booking', 'is_read')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'booking', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('İlişkili Bilgiler', {
            'fields': ('booking', 'is_read')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'template', 'status', 'created_at', 'sent_at')
    list_filter = ('notification_type', 'status', 'template', 'created_at')
    search_fields = ('user__email', 'recipient_email', 'recipient_phone', 'subject')
    readonly_fields = ('id', 'created_at', 'sent_at', 'provider_response')
    ordering = ('-created_at',)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'email_booking_confirmation', 'email_booking_reminder', 
        'sms_booking_confirmation', 'sms_booking_reminder'
    )
    search_fields = ('user__email',)


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['send_test_notification']
    
    def send_test_notification(self, request, queryset):
        """Send test notification to selected devices."""
        import logging
        logger = logging.getLogger(__name__)
        
        success_count = 0
        fail_count = 0
        error_messages = []
        
        # Initialize Firebase first
        FCMService.initialize()
        
        for device in queryset:
            if device.is_active:
                try:
                    logger.info(f'Sending test notification to token: {device.token[:20]}...')
                    result = FCMService.send_notification(
                        token=device.token,
                        title='🔔 Test Bildirimi',
                        body='Bu bir test bildirimidir. FCM çalışıyor! ✅',
                        data={
                            'type': 'test',
                            'url': '/admin/dashboard'
                        }
                    )
                    
                    if result:
                        success_count += 1
                        logger.info(f'Successfully sent to {device.token[:20]}...')
                    else:
                        fail_count += 1
                        error_msg = f'Failed to send to {device.user.email if device.user else "unknown"}'
                        error_messages.append(error_msg)
                        logger.warning(error_msg)
                except Exception as e:
                    fail_count += 1
                    error_msg = f'Error sending to {device.user.email if device.user else "unknown"}: {str(e)}'
                    error_messages.append(error_msg)
                    logger.error(error_msg)
            else:
                fail_count += 1
                error_messages.append(f'Device for {device.user.email if device.user else "unknown"} is not active')
        
        if success_count > 0:
            self.message_user(
                request,
                f'✅ {success_count} cihaza test bildirimi gönderildi.',
                messages.SUCCESS
            )
        
        if fail_count > 0:
            error_details = ' | '.join(error_messages[:3])  # Show first 3 errors
            self.message_user(
                request,
                f'❌ {fail_count} cihaza bildirim gönderilemedi. Detay: {error_details}',
                messages.ERROR
            )
    
    send_test_notification.short_description = "Seçili cihazlara test bildirimi gönder"
