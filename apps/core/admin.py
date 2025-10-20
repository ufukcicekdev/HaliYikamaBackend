from django.contrib import admin
from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'business_email', 'updated_at']
    
    fieldsets = (
        ('Bildirim Ayarları', {
            'fields': ('notification_sound', 'notification_email_enabled', 'notification_sms_enabled'),
            'description': 'Bildirim sesi sadece .mp3 formatında olmalıdır.'
        }),
        ('İşletme Bilgileri', {
            'fields': ('business_name', 'business_email', 'business_phone', 'business_address')
        }),
        ('Çalışma Saatleri', {
            'fields': ('working_hours_start', 'working_hours_end')
        }),
    )
    
    def has_add_permission(self, request):
        # Only one instance allowed
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Cannot delete system settings
        return False
