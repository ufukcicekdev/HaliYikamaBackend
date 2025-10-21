from django.db import models
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


class Booking(models.Model):
    """Customer booking/order."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    booking_number = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Rezervasyon Numarası")
    
    # User & Location
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='bookings', verbose_name="Kullanıcı")
    pickup_address = models.ForeignKey('accounts.Address', on_delete=models.PROTECT, related_name='pickup_bookings', verbose_name="Alım Adresi")
    delivery_address = models.ForeignKey(
        'accounts.Address', 
        on_delete=models.PROTECT, 
        related_name='delivery_bookings',
        null=True,
        blank=True,
        help_text='If different from pickup',
        verbose_name="Teslim Adresi"
    )
    
    # Scheduling
    pickup_date = models.DateField(verbose_name="Alım Tarihi")
    pickup_time_slot = models.ForeignKey(
        'TimeSlot', 
        on_delete=models.PROTECT, 
        related_name='pickup_bookings',
        null=True,
        blank=True,
        verbose_name="Alım Saat Aralığı"
    )
    delivery_date = models.DateField(null=True, blank=True, verbose_name="Teslim Tarihi")
    delivery_time_slot = models.ForeignKey(
        'TimeSlot', 
        on_delete=models.PROTECT, 
        related_name='delivery_bookings',
        null=True,
        blank=True,
        verbose_name="Teslim Saat Aralığı"
    )
    
    # Status & Assignment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    assigned_technician = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_bookings',
        limit_choices_to={'user_type': 'technician'},
        verbose_name="Atanan Teknisyen"
    )
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], verbose_name="Ara Toplam")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Teslimat Ücreti")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="İndirim")
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Toplam")
    currency = models.CharField(max_length=3, default='TRY', verbose_name="Para Birimi")
    
    # Notes
    customer_notes = models.TextField(blank=True, verbose_name="Müşteri Notları")
    admin_notes = models.TextField(blank=True, verbose_name="Admin Notları")
    cancellation_reason = models.TextField(blank=True, verbose_name="İptal Nedeni")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Onaylanma Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="İptal Tarihi")
    
    class Meta:
        verbose_name = 'Rezervasyon'
        verbose_name_plural = 'Rezervasyonlar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'pickup_date']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['booking_number']),
        ]
    
    def __str__(self):
        return f"{self.booking_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Generate unique booking number
            import random
            import string
            from django.utils import timezone
            now = timezone.now()
            self.booking_number = f"BK{now.year}{random.randint(10000, 99999)}"
        
        # Calculate total
        self.total = self.subtotal + self.delivery_fee - self.discount
        
        super().save(*args, **kwargs)
    
    def can_cancel(self):
        """Check if booking can be cancelled based on admin-defined rules."""
        from apps.services.models import BookingSettings
        
        if self.status in ['completed', 'cancelled']:
            return False, 'Booking is already completed or cancelled'
        
        settings = BookingSettings.get_settings()
        now = timezone.now()
        
        # If no time slot (e.g., carpet cleaning), use pickup date at midnight
        from datetime import datetime, time
        if self.pickup_time_slot:
            pickup_datetime = datetime.combine(self.pickup_date, self.pickup_time_slot.start_time)
        else:
            pickup_datetime = datetime.combine(self.pickup_date, time(0, 0))
        pickup_datetime = timezone.make_aware(pickup_datetime)
        
        time_until_pickup = pickup_datetime - now
        min_notice = timedelta(hours=settings.min_cancellation_notice_hours)
        
        if time_until_pickup < min_notice:
            hours_needed = settings.min_cancellation_notice_hours
            return False, f'Cancellation requires at least {hours_needed} hours notice'
        
        return True, ''
    
    def can_reschedule(self):
        """Check if booking can be rescheduled based on admin-defined rules."""
        from apps.services.models import BookingSettings
        
        if self.status in ['completed', 'cancelled']:
            return False, 'Booking is already completed or cancelled'
        
        settings = BookingSettings.get_settings()
        now = timezone.now()
        
        # If no time slot (e.g., carpet cleaning), use pickup date at midnight
        from datetime import datetime, time
        if self.pickup_time_slot:
            pickup_datetime = datetime.combine(self.pickup_date, self.pickup_time_slot.start_time)
        else:
            pickup_datetime = datetime.combine(self.pickup_date, time(0, 0))
        pickup_datetime = timezone.make_aware(pickup_datetime)
        
        time_until_pickup = pickup_datetime - now
        min_notice = timedelta(hours=settings.min_reschedule_notice_hours)
        
        if time_until_pickup < min_notice:
            hours_needed = settings.min_reschedule_notice_hours
            return False, f'Rescheduling requires at least {hours_needed} hours notice'
        
        return True, ''


class BookingItem(models.Model):
    """Individual items in a booking."""
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items', verbose_name="Rezervasyon")
    subtype = models.ForeignKey('services.SubType', on_delete=models.PROTECT, verbose_name="Alt Kategori")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Quantity or square meters',
        verbose_name="Miktar"
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyat")
    line_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satır Toplam")
    notes = models.TextField(blank=True, verbose_name="Notlar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = 'Rezervasyon Kalemi'
        verbose_name_plural = 'Rezervasyon Kalemleri'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.booking.booking_number} - {self.subtype.name}"
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class TimeSlot(models.Model):
    """Available time slots for pickups/deliveries."""
    
    date = models.DateField(verbose_name="Tarih")
    start_time = models.TimeField(verbose_name="Başlangıç Saati")
    end_time = models.TimeField(verbose_name="Bitiş Saati")
    max_capacity = models.IntegerField(default=5, verbose_name="Maksimum Kapasite")
    current_bookings = models.IntegerField(default=0, verbose_name="Mevcut Rezervasyonlar")
    is_available = models.BooleanField(default=True, verbose_name="Müsait")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = 'Zaman Aralığı'
        verbose_name_plural = 'Zaman Aralıkları'
        ordering = ['date', 'start_time']
        unique_together = [['date', 'start_time']]
        indexes = [
            models.Index(fields=['date', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} ({self.current_bookings}/{self.max_capacity})"
    
    def is_slot_available(self):
        """Check if slot has capacity."""
        return self.is_available and self.current_bookings < self.max_capacity
    
    def increment_bookings(self):
        """Increment booking count."""
        self.current_bookings += 1
        if self.current_bookings >= self.max_capacity:
            self.is_available = False
        self.save()
    
    def decrement_bookings(self):
        """Decrement booking count (on cancellation)."""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            self.is_available = True
            self.save()


class BookingStatusHistory(models.Model):
    """Track status changes for bookings."""
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history', verbose_name="Rezervasyon")
    old_status = models.CharField(max_length=20, verbose_name="Eski Durum")
    new_status = models.CharField(max_length=20, verbose_name="Yeni Durum")
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, verbose_name="Değiştiren")
    notes = models.TextField(blank=True, verbose_name="Notlar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Değiştirme Tarihi")
    
    class Meta:
        verbose_name = 'Rezervasyon Durum Geçmişi'
        verbose_name_plural = 'Rezervasyon Durum Geçmişleri'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.booking.booking_number}: {self.old_status} → {self.new_status}"
