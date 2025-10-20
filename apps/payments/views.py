from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Transaction, Refund, WebhookLog
from .serializers import TransactionSerializer, RefundSerializer, PaymentInitiateSerializer
from apps.bookings.models import Booking
from .services import IyzicoPaymentService


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """User transactions."""
    
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')


class PaymentViewSet(viewsets.ViewSet):
    """Payment operations."""
    
    permission_classes = (IsAuthenticated,)
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate payment for a booking."""
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking = get_object_or_404(Booking, id=serializer.validated_data['booking_id'], user=request.user)
        
        if booking.status != 'pending':
            return Response({
                'success': False,
                'error': 'Booking is not in pending status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize payment service (iyzico)
        payment_service = IyzicoPaymentService()
        
        try:
            result = payment_service.process_payment(
                booking=booking,
                user=request.user,
                payment_data=serializer.validated_data,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'Payment processed successfully',
                    'data': {
                        'transaction_id': result['transaction_id'],
                        'three_ds_url': result.get('three_ds_url'),  # For 3D Secure
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Payment failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def callback(self, request):
        """3D Secure callback endpoint."""
        # Handle 3D Secure callback
        payment_service = IyzicoPaymentService()
        result = payment_service.handle_3ds_callback(request.data)
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Payment completed',
                'booking_id': result.get('booking_id')
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)


class WebhookView(views.APIView):
    """Payment gateway webhooks."""
    
    permission_classes = (AllowAny,)
    
    def post(self, request, gateway):
        """Handle incoming webhooks."""
        # Log webhook
        webhook_log = WebhookLog.objects.create(
            gateway=gateway,
            event_type=request.data.get('event_type', 'unknown'),
            payload=request.data,
            headers=dict(request.headers)
        )
        
        try:
            if gateway == 'iyzico':
                payment_service = IyzicoPaymentService()
                payment_service.handle_webhook(request.data, webhook_log)
            elif gateway == 'stripe':
                # TODO: Implement Stripe webhook handling
                pass
            
            webhook_log.processed = True
            webhook_log.save()
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            webhook_log.error_message = str(e)
            webhook_log.save()
            return Response({'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)
