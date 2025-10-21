from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class FCMDevice(models.Model):
    """Firebase Cloud Messaging device tokens."""
    
    DEVICE_TYPE_CHOICES = [
        ('web', _('Web')),
        ('ios', _('iOS')),
        ('android', _('Android')),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='fcm_devices',
        null=True,
        blank=True
    )
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES, default='web')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FCM device')
        verbose_name_plural = _('FCM devices')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{user_email} - {self.get_device_type_display()}"


class AdminNotification(models.Model):
    """In-app notifications for admin users."""
    
    TYPE_CHOICES = [
        ('new_order', _('New Order')),
        ('cancelled_order', _('Cancelled Order')),
        ('status_change', _('Status Change')),
        ('info', _('Information')),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='admin_notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('admin notification')
        verbose_name_plural = _('admin notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"


class Notification(models.Model):
    """Email and SMS notifications."""
    
    TYPE_CHOICES = [
        ('email', _('Email')),
        ('sms', _('SMS')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    ]
    
    TEMPLATE_CHOICES = [
        ('booking_confirmation', _('Booking Confirmation')),
        ('booking_reminder', _('Booking Reminder')),
        ('booking_cancellation', _('Booking Cancellation')),
        ('booking_rescheduled', _('Booking Rescheduled')),
        ('technician_assigned', _('Technician Assigned')),
        ('payment_success', _('Payment Successful')),
        ('payment_failed', _('Payment Failed')),
        ('refund_processed', _('Refund Processed')),
        ('account_verification', _('Account Verification')),
        ('password_reset', _('Password Reset')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    template = models.CharField(max_length=50, choices=TEMPLATE_CHOICES)
    
    # Email fields
    recipient_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255, blank=True)
    
    # SMS fields
    recipient_phone = models.CharField(max_length=20, blank=True)
    
    # Common
    message = models.TextField()
    context_data = models.JSONField(default=dict, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.email}"


class UserNotification(models.Model):
    """In-app notifications for customers."""
    
    TYPE_CHOICES = [
        ('order_confirmed', _('Order Confirmed')),
        ('order_in_progress', _('Order In Progress')),
        ('order_completed', _('Order Completed')),
        ('order_cancelled', _('Order Cancelled')),
        ('info', _('Information')),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='info')
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('user notification')
        verbose_name_plural = _('user notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.email}"


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_preferences')
    
    email_booking_confirmation = models.BooleanField(default=True)
    email_booking_reminder = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    sms_booking_confirmation = models.BooleanField(default=True)
    sms_booking_reminder = models.BooleanField(default=True)
    sms_marketing = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')
    
    def __str__(self):
        return f"{self.user.email} - Preferences"
