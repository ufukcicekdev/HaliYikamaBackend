from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _


class SystemSettings(models.Model):
    """System-wide settings (singleton model)."""
    
    # Notification settings
    notification_sound = models.FileField(
        upload_to='sounds/',
        validators=[FileExtensionValidator(allowed_extensions=['mp3'])],
        null=True,
        blank=True,
        verbose_name=_('Bildirim Sesi'),
        help_text=_('Yönetici bildirimleri için ses dosyası (.mp3 formatında)')
    )
    
    # Email settings
    notification_email_enabled = models.BooleanField(
        default=True,
        verbose_name=_('E-posta Bildirimleri Aktif')
    )
    notification_sms_enabled = models.BooleanField(
        default=True,
        verbose_name=_('SMS Bildirimleri Aktif')
    )
    
    # Business info
    business_name = models.CharField(
        max_length=255,
        default='Halı Yıkama',
        verbose_name=_('İşletme Adı')
    )
    business_email = models.EmailField(
        default='info@haliyikama.com',
        verbose_name=_('İşletme E-postası')
    )
    business_phone = models.CharField(
        max_length=20,
        default='+90 555 123 4567',
        verbose_name=_('İşletme Telefonu')
    )
    business_address = models.TextField(
        default='İstanbul, Türkiye',
        verbose_name=_('İşletme Adresi')
    )
    
    # Working hours
    working_hours_start = models.TimeField(
        default='09:00',
        verbose_name=_('Çalışma Saati Başlangıç')
    )
    working_hours_end = models.TimeField(
        default='18:00',
        verbose_name=_('Çalışma Saati Bitiş')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Sistem Ayarları')
        verbose_name_plural = _('Sistem Ayarları')
    
    def __str__(self):
        return 'Sistem Ayarları'
    
    @classmethod
    def get_settings(cls):
        """Get or create singleton instance."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion."""
        pass
