"""Background tasks for notifications."""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from twilio.rest import Client
from .models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_email_notification(notification_id):
    """Send email notification."""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Send email
        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient_email],
            fail_silently=False,
        )
        
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        
        return f"Email sent to {notification.recipient_email}"
        
    except Exception as e:
        notification.status = 'failed'
        notification.error_message = str(e)
        notification.save()
        raise


def send_sms_notification(notification_id):
    """Send SMS notification."""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if not settings.TWILIO_ACCOUNT_SID:
            raise ValueError("Twilio not configured")
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=notification.message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=notification.recipient_phone
        )
        
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.provider_response = {
            'sid': message.sid,
            'status': message.status
        }
        notification.save()
        
        return f"SMS sent to {notification.recipient_phone}"
        
    except Exception as e:
        notification.status = 'failed'
        notification.error_message = str(e)
        notification.save()
        raise


def send_booking_reminders():
    """
    Send booking reminders for upcoming pickups.
    This runs daily via Celery Beat.
    """
    from apps.bookings.models import Booking
    from datetime import timedelta
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Get bookings scheduled for tomorrow
    bookings = Booking.objects.filter(
        pickup_date=tomorrow,
        status__in=['confirmed', 'scheduled']
    ).select_related('user')
    
    for booking in bookings:
        # Create notification
        notification = Notification.objects.create(
            user=booking.user,
            booking=booking,
            notification_type='email',
            template='booking_reminder',
            recipient_email=booking.user.email,
            subject=f'Reminder: Pickup tomorrow for {booking.booking_number}',
            message=f'This is a reminder that your carpet cleaning pickup is scheduled for tomorrow.',
            context_data={'booking': str(booking.id)}
        )
        
        # Send email
        send_email_notification(str(notification.id))
        
        # Send SMS if enabled
        if booking.user.phone and booking.user.notification_preferences.sms_booking_reminder:
            sms_notification = Notification.objects.create(
                user=booking.user,
                booking=booking,
                notification_type='sms',
                template='booking_reminder',
                recipient_phone=str(booking.user.phone),
                message=f'Reminder: Carpet cleaning pickup tomorrow. Booking: {booking.booking_number}',
                context_data={'booking': str(booking.id)}
            )
            send_sms_notification(str(sms_notification.id))
    
    return f"Sent reminders for {bookings.count()} bookings"


def send_booking_confirmation(booking):
    """Helper to send booking confirmation."""
    notification = Notification.objects.create(
        user=booking.user,
        booking=booking,
        notification_type='email',
        template='booking_confirmation',
        recipient_email=booking.user.email,
        subject=f'Booking Confirmed: {booking.booking_number}',
        message=f'Your booking has been confirmed. Pickup date: {booking.pickup_date}',
        context_data={'booking': str(booking.id)}
    )
    
    send_email_notification(str(notification.id))
