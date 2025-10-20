from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg, F, DecimalField
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import Booking, TimeSlot, BookingStatusHistory
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingCreateSerializer,
    TimeSlotSerializer,
    BookingStatusUpdateSerializer,
    BookingStatusHistorySerializer,
)
from .permissions import IsBookingOwnerOrAdmin

User = get_user_model()


class BookingViewSet(viewsets.ModelViewSet):
    """Booking CRUD operations."""
    
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'pickup_date']
    search_fields = ['booking_number']
    ordering_fields = ['created_at', 'pickup_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type == 'admin':
            return Booking.objects.all().select_related(
                'user', 'pickup_address', 'pickup_time_slot'
            ).prefetch_related('items__subtype')
        return Booking.objects.filter(user=user).select_related(
            'pickup_address', 'pickup_time_slot'
        ).prefetch_related('items__subtype')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        return BookingDetailSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsBookingOwnerOrAdmin()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        # TODO: Trigger payment and send confirmation email
        
        return Response({
            'success': True,
            'message': 'Booking created successfully',
            'data': BookingDetailSerializer(booking).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()
        
        # Check if cancellation is allowed
        can_cancel, message = booking.can_cancel()
        if not can_cancel:
            return Response({
                'success': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status
        old_status = booking.status
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = request.data.get('reason', '')
        booking.save()
        
        # Record status change
        BookingStatusHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status='cancelled',
            changed_by=request.user,
            notes=booking.cancellation_reason
        )
        
        # Release time slots
        booking.pickup_time_slot.decrement_bookings()
        if booking.delivery_time_slot:
            booking.delivery_time_slot.decrement_bookings()
        
        # Calculate refund amount (if applicable)
        from apps.services.models import BookingSettings
        settings = BookingSettings.get_settings()
        
        refund_amount = booking.total
        if settings.cancellation_fee_percentage > 0:
            fee = (booking.total * settings.cancellation_fee_percentage) / 100
            refund_amount = booking.total - fee
        
        # TODO: Process refund via payment gateway
        
        return Response({
            'success': True,
            'message': 'Booking cancelled successfully',
            'data': BookingDetailSerializer(booking).data,
            'refund_amount': str(refund_amount)
        })
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule a booking."""
        booking = self.get_object()
        
        # Check if rescheduling is allowed
        can_reschedule, message = booking.can_reschedule()
        if not can_reschedule:
            return Response({
                'success': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get new slot details
        new_pickup_slot_id = request.data.get('new_pickup_slot_id')
        new_delivery_slot_id = request.data.get('new_delivery_slot_id')
        
        if not new_pickup_slot_id:
            return Response({
                'success': False,
                'error': 'New pickup slot is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_pickup_slot = TimeSlot.objects.get(id=new_pickup_slot_id)
            if not new_pickup_slot.is_slot_available():
                return Response({
                    'success': False,
                    'error': 'Selected time slot is not available'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Release old slots
            old_pickup_slot = booking.pickup_time_slot
            old_delivery_slot = booking.delivery_time_slot
            
            # Update booking
            booking.pickup_time_slot = new_pickup_slot
            booking.pickup_date = new_pickup_slot.date
            
            if new_delivery_slot_id:
                new_delivery_slot = TimeSlot.objects.get(id=new_delivery_slot_id)
                if not new_delivery_slot.is_slot_available():
                    return Response({
                        'success': False,
                        'error': 'Selected delivery slot is not available'
                    }, status=status.HTTP_400_BAD_REQUEST)
                booking.delivery_time_slot = new_delivery_slot
                booking.delivery_date = new_delivery_slot.date
            
            booking.save()
            
            # Update slot capacities
            old_pickup_slot.decrement_bookings()
            new_pickup_slot.increment_bookings()
            
            if old_delivery_slot and new_delivery_slot_id:
                old_delivery_slot.decrement_bookings()
                new_delivery_slot = TimeSlot.objects.get(id=new_delivery_slot_id)
                new_delivery_slot.increment_bookings()
            
            # Record status change
            BookingStatusHistory.objects.create(
                booking=booking,
                old_status=booking.status,
                new_status='scheduled',
                changed_by=request.user,
                notes='Booking rescheduled by customer'
            )
            
            # TODO: Send rescheduling notification
            
            return Response({
                'success': True,
                'message': 'Booking rescheduled successfully',
                'data': BookingDetailSerializer(booking).data
            })
            
        except TimeSlot.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid time slot'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Create a new booking based on a previous one."""
        original_booking = self.get_object()
        
        # Create a new booking with same items but no dates/slots
        new_booking_data = {
            'pickup_address': original_booking.pickup_address.id,
            'delivery_address': original_booking.delivery_address.id if original_booking.delivery_address else None,
            'customer_notes': request.data.get('notes', ''),
            'items': []
        }
        
        # Copy items from original booking
        for item in original_booking.items.all():
            new_booking_data['items'].append({
                'subtype_id': item.subtype.id,
                'quantity': float(item.quantity),
                'notes': item.notes
            })
        
        # Return the data for frontend to continue booking flow
        return Response({
            'success': True,
            'message': 'Reorder data prepared. Please select date and time.',
            'data': new_booking_data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Admin: Update booking status."""
        booking = self.get_object()
        serializer = BookingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_status = booking.status
        new_status = serializer.validated_data['status']
        
        booking.status = new_status
        if new_status == 'confirmed':
            booking.confirmed_at = timezone.now()
        elif new_status == 'completed':
            booking.completed_at = timezone.now()
        elif new_status == 'cancelled':
            booking.cancelled_at = timezone.now()
        booking.save()
        
        # Record status change
        BookingStatusHistory.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        
        return Response({
            'success': True,
            'message': 'Booking status updated',
            'data': BookingDetailSerializer(booking).data
        })
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """Get booking status history."""
        booking = self.get_object()
        history = booking.status_history.all()
        serializer = BookingStatusHistorySerializer(history, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    """Available time slots."""
    
    serializer_class = TimeSlotSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'is_available']
    
    def get_queryset(self):
        # Only show future slots
        today = timezone.now().date()
        queryset = TimeSlot.objects.filter(date__gte=today)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('date', 'start_time')
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get only available slots."""
        queryset = self.get_queryset().filter(is_available=True)
        
        # Group by date
        slots_by_date = {}
        for slot in queryset:
            date_str = slot.date.isoformat()
            if date_str not in slots_by_date:
                slots_by_date[date_str] = []
            slots_by_date[date_str].append(TimeSlotSerializer(slot).data)
        
        return Response({
            'success': True,
            'data': slots_by_date
        })


# Admin-only endpoints

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_customers(request):
    """Get all customers with stats."""
    customers = User.objects.filter(
        user_type='customer',
        is_staff=False
    ).annotate(
        total_bookings=Count('bookings'),
        total_spent=Sum('bookings__total')
    ).order_by('-date_joined')
    
    customer_data = []
    for customer in customers:
        last_booking = customer.bookings.order_by('-created_at').first()
        customer_data.append({
            'id': customer.id,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': str(customer.phone) if customer.phone else '',
            'date_joined': customer.date_joined.isoformat(),
            'total_bookings': customer.total_bookings or 0,
            'total_spent': float(customer.total_spent or 0),
            'last_booking_date': last_booking.created_at.isoformat() if last_booking else None,
        })
    
    return Response({
        'success': True,
        'data': customer_data
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_customer_detail(request, customer_id):
    """Get customer details with bookings and addresses."""
    try:
        customer = User.objects.get(id=customer_id, user_type='customer')
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Customer not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get customer stats
    total_bookings = customer.bookings.count()
    total_spent = customer.bookings.aggregate(total=Sum('total'))['total'] or 0
    
    # Get bookings
    bookings = customer.bookings.all().order_by('-created_at')
    booking_data = []
    for booking in bookings:
        booking_data.append({
            'id': booking.id,
            'service_date': booking.pickup_date.isoformat(),
            'service_time': booking.pickup_time_slot.start_time.strftime('%H:%M') if booking.pickup_time_slot else '',
            'status': booking.status,
            'total_price': float(booking.total),
            'created_at': booking.created_at.isoformat(),
        })
    
    # Get addresses
    addresses = customer.addresses.all()
    address_data = []
    for addr in addresses:
        address_data.append({
            'id': addr.id,
            'title': addr.title,
            'district': addr.district.name if addr.district else '',
            'full_address': addr.full_address,
            'is_default': addr.is_default,
        })
    
    return Response({
        'success': True,
        'data': {
            'id': customer.id,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': str(customer.phone) if customer.phone else '',
            'date_joined': customer.date_joined.isoformat(),
            'total_bookings': total_bookings,
            'total_spent': float(total_spent),
            'addresses': address_data,
            'bookings': booking_data,
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_reports(request):
    """Get admin reports and statistics."""
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get bookings in date range
    bookings = Booking.objects.filter(created_at__gte=start_date)
    
    # Calculate stats
    stats = {
        'total_revenue': float(bookings.aggregate(total=Sum('total'))['total'] or 0),
        'total_bookings': bookings.count(),
        'total_customers': User.objects.filter(user_type='customer').count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'pending_bookings': bookings.filter(status='pending').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
        'average_order_value': float(bookings.aggregate(avg=Avg('total'))['avg'] or 0),
    }
    
    # Revenue data by date
    revenue_data = []
    current_date = start_date.date()
    end_date = timezone.now().date()
    
    while current_date <= end_date:
        day_bookings = bookings.filter(created_at__date=current_date)
        revenue_data.append({
            'date': current_date.isoformat(),
            'revenue': float(day_bookings.aggregate(total=Sum('total'))['total'] or 0),
            'bookings': day_bookings.count(),
        })
        current_date += timedelta(days=1)
    
    return Response({
        'success': True,
        'data': {
            'stats': stats,
            'revenue_data': revenue_data,
        }
    })


@api_view(['GET', 'PUT'])
@permission_classes([IsAdminUser])
def admin_settings(request):
    """Get or update admin settings."""
    from apps.services.models import BookingSettings
    
    settings = BookingSettings.get_settings()
    
    if request.method == 'GET':
        return Response({
            'success': True,
            'data': {
                'business_name': 'Halı Yıkama',
                'business_email': 'info@haliyikama.com',
                'business_phone': '+90 555 123 4567',
                'business_address': 'İstanbul, Türkiye',
                'working_hours_start': '09:00',
                'working_hours_end': '18:00',
                'booking_advance_days': settings.booking_advance_days,
                'min_booking_amount': float(settings.min_order_amount),
                'tax_rate': 20,
                'email_notifications': True,
                'sms_notifications': True,
                'auto_confirm_bookings': False,
            }
        })
    
    elif request.method == 'PUT':
        # Update settings
        data = request.data
        
        if 'booking_advance_days' in data:
            settings.booking_advance_days = int(data['booking_advance_days'])
        if 'min_booking_amount' in data:
            settings.min_order_amount = float(data['min_booking_amount'])
        
        settings.save()
        
        return Response({
            'success': True,
            'message': 'Settings updated successfully'
        })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """Get admin dashboard statistics."""
    today = timezone.now().date()
    
    # Total bookings
    total_bookings = Booking.objects.count()
    
    # Today's bookings
    today_bookings = Booking.objects.filter(created_at__date=today).count()
    
    # This month's bookings
    month_start = today.replace(day=1)
    month_bookings = Booking.objects.filter(created_at__date__gte=month_start).count()
    
    # Pending bookings
    pending_bookings = Booking.objects.filter(status='pending').count()
    
    # Revenue stats
    total_revenue = Booking.objects.filter(
        status__in=['completed', 'confirmed', 'in_progress']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    today_revenue = Booking.objects.filter(
        created_at__date=today,
        status__in=['completed', 'confirmed', 'in_progress']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    month_revenue = Booking.objects.filter(
        created_at__date__gte=month_start,
        status__in=['completed', 'confirmed', 'in_progress']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Active customers
    active_customers = User.objects.filter(
        bookings__isnull=False,
        is_active=True
    ).distinct().count()
    
    # Status breakdown
    status_breakdown = Booking.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent revenue trend (last 7 days)
    seven_days_ago = today - timedelta(days=6)
    revenue_trend = Booking.objects.filter(
        created_at__date__gte=seven_days_ago,
        status__in=['completed', 'confirmed', 'in_progress']
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total')
    ).order_by('date')
    
    return Response({
        'success': True,
        'data': {
            'total_bookings': total_bookings,
            'today_bookings': today_bookings,
            'month_bookings': month_bookings,
            'pending_bookings': pending_bookings,
            'total_revenue': str(total_revenue),
            'today_revenue': str(today_revenue),
            'month_revenue': str(month_revenue),
            'active_customers': active_customers,
            'status_breakdown': list(status_breakdown),
            'revenue_trend': [
                {
                    'date': item['date'].isoformat(),
                    'revenue': str(item['revenue'])
                }
                for item in revenue_trend
            ]
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_recent_bookings(request):
    """Get recent bookings for admin dashboard."""
    limit = int(request.GET.get('limit', 10))
    
    bookings = Booking.objects.select_related(
        'user', 'pickup_address', 'pickup_time_slot'
    ).prefetch_related(
        'items__subtype'
    ).order_by('-created_at')[:limit]
    
    serializer = BookingListSerializer(bookings, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })
