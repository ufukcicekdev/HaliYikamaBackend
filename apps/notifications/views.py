from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import AdminNotification, FCMDevice, UserNotification
from .serializers import AdminNotificationSerializer, FCMDeviceSerializer, UserNotificationSerializer


class IsAdminOrStaff(IsAuthenticated):
    """
    Custom permission to allow access to admin users (is_staff=True or user_type='admin').
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_staff or getattr(request.user, 'user_type', None) == 'admin'


class AdminNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin notifications.
    """
    queryset = AdminNotification.objects.all()
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAdminOrStaff]
    
    def get_queryset(self):
        queryset = AdminNotification.objects.all()
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        AdminNotification.objects.filter(is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(self.serializer_class(notification).data)


class UserNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for customer/user notifications.
    """
    queryset = UserNotification.objects.all()
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only return notifications for the current user
        queryset = UserNotification.objects.filter(user=self.request.user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for current user."""
        UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for current user."""
        count = UserNotification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(self.serializer_class(notification).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    """
    Save or update FCM device token for push notifications.
    """
    token = request.data.get('token')
    device_type = request.data.get('device_type', 'web')
    
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create device
    device, created = FCMDevice.objects.update_or_create(
        token=token,
        defaults={
            'user': request.user,
            'device_type': device_type,
            'is_active': True
        }
    )
    
    serializer = FCMDeviceSerializer(device)
    
    return Response({
        'success': True,
        'data': serializer.data,
        'message': 'FCM token saved successfully'
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminOrStaff])
def send_test_notification(request):
    """
    Send a test FCM notification to all admin users.
    """
    from .fcm_service import FCMService
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Check if there are any FCM devices
        device_count = FCMDevice.objects.filter(is_active=True).count()
        
        if device_count == 0:
            return Response({
                'success': False,
                'error': 'No FCM devices registered. Please enable notifications first.',
                'device_count': 0
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f'Sending test notification to {device_count} devices')
        
        result = FCMService.send_to_admin_users(
            title='🔔 Test Notification',
            body='This is a test notification. FCM is working! ✅',
            data={
                'type': 'test',
                'url': '/admin/dashboard'
            }
        )
        
        # Always create an in-app notification for testing
        AdminNotification.objects.create(
            title='Test Notification',
            message='This is a test notification to verify FCM is working.',
            notification_type='info',
            is_read=False
        )
        
        if result:
            return Response({
                'success': True,
                'message': f'Test notification sent to {device_count} device(s)',
                'device_count': device_count
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to send notification. Check Firebase configuration and Django logs.',
                'device_count': device_count
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f'Error sending test notification: {str(e)}', exc_info=True)
        return Response(
            {
                'success': False,
                'error': f'Error: {str(e)}',
                'details': 'Check Django logs for full error details'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
