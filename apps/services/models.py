from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class District(models.Model):
    """Istanbul districts where service is available."""
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Bölge Adı")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    delivery_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Teslimat Ücreti"
    )
    order_priority = models.IntegerField(default=0, help_text='Lower numbers appear first', verbose_name="Sıralama Önceliği")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Bölge'
        verbose_name_plural = 'Bölgeler'
        ordering = ['order_priority', 'name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Service categories (carpets, sofas, duvets, etc.)."""
    
    PRICING_TYPE_CHOICES = [
        ('per_sqm', 'Per Square Meter'),
        ('per_item', 'Per Item'),
        ('per_seat', 'Per Seat'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Kategori Adı")
    slug = models.SlugField(unique=True, verbose_name="Kısa Ad")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class or emoji', verbose_name="İkon")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Resim")
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES, verbose_name="Fiyatlandırma Tipi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    order_priority = models.IntegerField(default=0, help_text='Lower numbers appear first', verbose_name="Sıralama Önceliği")
    
    # Scheduling settings
    requires_time_selection = models.BooleanField(
        default=False,
        help_text='If true, customers must select a time slot (e.g., sofa cleaning)',
        verbose_name="Saat Seçimi Gerekli"
    )
    requires_pickup_delivery = models.BooleanField(
        default=False,
        help_text='If true, requires separate pickup and delivery dates (e.g., carpet cleaning)',
        verbose_name="Alım-Teslim Gerekli"
    )
    min_days_between_pickup_delivery = models.IntegerField(
        default=7,
        help_text='Minimum days required between pickup and delivery dates',
        verbose_name="Alım-Teslim Arası Min. Gün"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategoriler'
        ordering = ['order_priority', 'name']
    
    def __str__(self):
        return self.name


class SubType(models.Model):
    """Subtypes within categories (kilim, wool rug, 1-seater, etc.)."""
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subtypes', verbose_name="Kategori")
    name = models.CharField(max_length=100, verbose_name="Alt Kategori Adı")
    slug = models.SlugField(verbose_name="Kısa Ad")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class or emoji', verbose_name="İkon")
    image = models.ImageField(upload_to='subtypes/', blank=True, null=True, verbose_name="Resim")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    order_priority = models.IntegerField(default=0, verbose_name="Sıralama Önceliği")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Alt Kategori'
        verbose_name_plural = 'Alt Kategoriler'
        ordering = ['order_priority', 'name']
        unique_together = [['category', 'slug']]
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Pricing(models.Model):
    """Dynamic pricing for each subtype."""
    
    subtype = models.ForeignKey(SubType, on_delete=models.CASCADE, related_name='pricing', verbose_name="Alt Kategori")
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Temel Fiyat"
    )
    currency = models.CharField(max_length=3, default='TRY', verbose_name="Para Birimi")
    
    # Optional seasonal/promotional pricing
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="İndirim %"
    )
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name="Geçerlilik Başlangıcı")
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="Geçerlilik Bitişi")
    
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Fiyatlandırma'
        verbose_name_plural = 'Fiyatlandırmalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subtype.name} - {self.base_price} {self.currency}"
    
    def get_final_price(self):
        """Calculate final price with discount."""
        if self.discount_percentage > 0:
            discount_amount = (self.base_price * self.discount_percentage) / 100
            return self.base_price - discount_amount
        return self.base_price


class WorkingHours(models.Model):
    """Admin-configurable working hours and time slot settings."""
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, unique=True, verbose_name="Gün")
    is_working_day = models.BooleanField(default=True, verbose_name="Çalışma Günü")
    opening_time = models.TimeField(default='08:00', help_text='Default: 08:00', verbose_name="Açılış Saati")
    closing_time = models.TimeField(default='00:00', help_text='Default: 00:00 (midnight)', verbose_name="Kapanış Saati")
    slot_duration_minutes = models.IntegerField(default=60, help_text='Duration of each time slot', verbose_name="Slot Süresi (Dakika)")
    max_bookings_per_slot = models.IntegerField(default=5, help_text='Maximum concurrent bookings', verbose_name="Slot Başına Max. Rezervasyon")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Çalışma Saatleri'
        verbose_name_plural = 'Çalışma Saatleri'
        ordering = ['weekday']
    
    def __str__(self):
        return f"{self.get_weekday_display()}: {self.opening_time} - {self.closing_time}"


class Holiday(models.Model):
    """Public holidays and special non-working dates."""
    
    date = models.DateField(unique=True, verbose_name="Tarih")
    name = models.CharField(max_length=100, verbose_name="Tatil Adı")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = 'Tatil'
        verbose_name_plural = 'Tatiller'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.name}"


class BookingSettings(models.Model):
    """Global booking and cancellation rules (singleton model)."""
    
    # Cancellation rules
    min_cancellation_notice_hours = models.IntegerField(
        default=2,
        help_text='Minimum hours before booking to allow cancellation (default: 2)',
        verbose_name="Min. İptal Bildirimi (Saat)"
    )
    min_reschedule_notice_hours = models.IntegerField(
        default=2,
        help_text='Minimum hours before booking to allow rescheduling (default: 2)',
        verbose_name="Min. Yeniden Planlama Bildirimi (Saat)"
    )
    
    # Penalties (optional)
    cancellation_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Percentage of total as cancellation fee (0-100)',
        verbose_name="İptal Ücreti %"
    )
    late_cancellation_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Additional fee for cancellations within notice period',
        verbose_name="Geç İptal Ücreti %"
    )
    
    # Service hours (global defaults)
    default_service_start_time = models.TimeField(
        default='08:00',
        help_text='Default service start time (08:00)',
        verbose_name="Varsayılan Hizmet Başlangıç Saati"
    )
    default_service_end_time = models.TimeField(
        default='00:00',
        help_text='Default service end time (00:00 = midnight)',
        verbose_name="Varsayılan Hizmet Bitiş Saati"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Rezervasyon Ayarları'
        verbose_name_plural = 'Rezervasyon Ayarları'
    
    def __str__(self):
        return "Booking Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
