from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.bookings.models import Booking
from .models import AdminNotification, UserNotification
from .fcm_service import FCMService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Booking)
def create_booking_notification(sender, instance, created, **kwargs):
    """Create admin notification when a new booking is created."""
    if created:
        # Create in-app notification
        AdminNotification.objects.create(
            title='Yeni Sipariş Geldi!',
            message=f'{instance.user.get_full_name()} tarafından yeni bir sipariş oluşturuldu. Sipariş No: #{instance.id}',
            notification_type='new_order',
            booking=instance,
            is_read=False
        )
        
        # Send FCM push notification to admins
        try:
            FCMService.send_to_admin_users(
                title='🔔 Yeni Sipariş Geldi!',
                body=f'{instance.user.get_full_name()} tarafından yeni bir sipariş oluşturuldu. Sipariş No: #{instance.id}',
                data={
                    'type': 'new_order',
                    'bookingId': str(instance.id),
                    'url': f'/admin/orders/{instance.id}'
                }
            )
            logger.info(f'FCM notification sent for new booking #{instance.id}')
        except Exception as e:
            logger.error(f'Error sending FCM notification for booking #{instance.id}: {e}')


@receiver(pre_save, sender=Booking)
def create_cancellation_notification(sender, instance, **kwargs):
    """Create admin notification when a booking is cancelled."""
    if instance.pk:  # Only for existing bookings
        try:
            old_instance = Booking.objects.get(pk=instance.pk)
            # Check if status changed to cancelled
            if old_instance.status != 'cancelled' and instance.status == 'cancelled':
                # Create in-app notification
                AdminNotification.objects.create(
                    title='Sipariş İptal Edildi',
                    message=f'#{instance.id} numaralı sipariş iptal edildi. Müşteri: {instance.user.get_full_name()}',
                    notification_type='cancelled_order',
                    booking=instance,
                    is_read=False
                )
                
                # Send FCM push notification
                try:
                    FCMService.send_to_admin_users(
                        title='❌ Sipariş İptal Edildi',
                        body=f'#{instance.id} numaralı sipariş iptal edildi. Müşteri: {instance.user.get_full_name()}',
                        data={
                            'type': 'cancelled_order',
                            'bookingId': str(instance.id),
                            'url': f'/admin/orders/{instance.id}'
                        }
                    )
                except Exception as e:
                    logger.error(f'Error sending FCM notification for cancelled booking #{instance.id}: {e}')
                    
            # Check for other status changes (send to CUSTOMER, not admin)
            elif old_instance.status != instance.status and instance.status != 'cancelled':
                status_names = {
                    'pending': 'Bekliyor',
                    'confirmed': 'Onaylandı',
                    'in_progress': 'İşlemde',
                    'completed': 'Tamamlandı',
                }
                new_status = status_names.get(instance.status, instance.status)
                
                # Create notification for CUSTOMER
                notification_messages = {
                    'confirmed': '✅ Siparişiniz Onaylandı!',
                    'in_progress': '🔄 Siparişiniz İşlemde!',
                    'completed': '✨ Siparişiniz Tamamlandı!',
                }
                
                notification_types = {
                    'confirmed': 'order_confirmed',
                    'in_progress': 'order_in_progress',
                    'completed': 'order_completed',
                }
                
                title = notification_messages.get(instance.status, 'Sipariş Durumu Değişti')
                notification_type = notification_types.get(instance.status, 'info')
                
                # Create in-app notification for CUSTOMER
                UserNotification.objects.create(
                    user=instance.user,  # Send to customer, not admin
                    title=title,
                    message=f'#{instance.id} numaralı siparişinizin durumu "{new_status}" olarak güncellendi.',
                    notification_type=notification_type,
                    booking=instance,
                    is_read=False
                )
                
                # Send FCM push notification to CUSTOMER
                try:
                    FCMService.send_to_user(
                        user=instance.user,
                        title=title,
                        body=f'#{instance.id} numaralı siparişinizin durumu "{new_status}" olarak güncellendi.',
                        data={
                            'type': 'status_change',
                            'bookingId': str(instance.id),
                            'url': f'/dashboard/siparisler/{instance.id}'
                        }
                    )
                except Exception as e:
                    logger.error(f'Error sending FCM notification to customer for status change #{instance.id}: {e}')
        except Booking.DoesNotExist:
            pass
