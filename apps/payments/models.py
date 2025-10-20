from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import uuid


class Transaction(models.Model):
    """Payment transactions."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_GATEWAY_CHOICES = [
        ('iyzico', 'iyzico'),
        ('stripe', 'Stripe'),
    ]
    
    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    transaction_id = models.CharField(max_length=100, unique=True, editable=False, verbose_name="İşlem Numarası")
    
    # Relations
    booking = models.ForeignKey('bookings.Booking', on_delete=models.PROTECT, related_name='transactions', verbose_name="Rezervasyon")
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='transactions', verbose_name="Kullanıcı")
    payment_method = models.ForeignKey(
        'accounts.PaymentMethod', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions',
        verbose_name="Ödeme Yöntemi"
    )
    
    # Payment details
    payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAY_CHOICES, verbose_name="Ödeme Gateway")
    gateway_transaction_id = models.CharField(max_length=255, blank=True, verbose_name="Gateway İşlem ID")
    gateway_response = models.JSONField(default=dict, blank=True, verbose_name="Gateway Yanıtı")
    
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    currency = models.CharField(max_length=3, default='TRY', verbose_name="Para Birimi")
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="İade Tutarı")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tamamlanma Tarihi")
    
    class Meta:
        verbose_name = 'İşlem'
        verbose_name_plural = 'İşlemler'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['gateway_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import random
            self.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


class Refund(models.Model):
    """Refund requests and processing."""
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='refunds', verbose_name="İşlem")
    booking = models.ForeignKey('bookings.Booking', on_delete=models.PROTECT, related_name='refunds', verbose_name="Rezervasyon")
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    reason = models.TextField(verbose_name="Neden")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested', verbose_name="Durum")
    
    admin_notes = models.TextField(blank=True, verbose_name="Admin Notları")
    gateway_refund_id = models.CharField(max_length=255, blank=True, verbose_name="Gateway İade ID")
    
    requested_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='requested_refunds', verbose_name="Talep Eden")
    processed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds', verbose_name="İşleyen")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Talep Tarihi")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="İşlenme Tarihi")
    
    class Meta:
        verbose_name = 'İade'
        verbose_name_plural = 'İadeler'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.id} - {self.amount}"


class WebhookLog(models.Model):
    """Log payment gateway webhooks for debugging."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID")
    gateway = models.CharField(max_length=20, verbose_name="Gateway")
    event_type = models.CharField(max_length=100, verbose_name="Olay Tipi")
    payload = models.JSONField(verbose_name="İçerik")
    headers = models.JSONField(default=dict, verbose_name="Header'lar")
    
    processed = models.BooleanField(default=False, verbose_name="İşlendi")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="İşlenme Tarihi")
    
    class Meta:
        verbose_name = 'Webhook Kaydı'
        verbose_name_plural = 'Webhook Kayıtları'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gateway', 'processed']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.gateway} - {self.event_type}"
