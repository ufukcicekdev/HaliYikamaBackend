from rest_framework import viewsets, filters, status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Transaction, Refund


class TransactionAdminSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id', 'transaction_id', 'created_at', 'updated_at')


class RefundAdminSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class TransactionStatusUpdateSerializer(drf_serializers.Serializer):
    status = drf_serializers.ChoiceField(choices=Transaction.STATUS_CHOICES)
    error_message = drf_serializers.CharField(required=False, allow_blank=True)


class RefundStatusUpdateSerializer(drf_serializers.Serializer):
    status = drf_serializers.ChoiceField(choices=Refund.STATUS_CHOICES)
    admin_notes = drf_serializers.CharField(required=False, allow_blank=True)
    gateway_refund_id = drf_serializers.CharField(required=False, allow_blank=True)


class TransactionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin: list and retrieve Transactions, update status."""
    queryset = Transaction.objects.all().select_related('booking', 'user', 'payment_method')
    serializer_class = TransactionAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_gateway', 'currency']
    search_fields = ['transaction_id', 'gateway_transaction_id', 'user__email']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update transaction status."""
        try:
            transaction = self.get_object()
            serializer = TransactionStatusUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            transaction.status = serializer.validated_data['status']
            if 'error_message' in serializer.validated_data:
                transaction.error_message = serializer.validated_data['error_message']
            if transaction.status == 'completed' and not transaction.completed_at:
                transaction.completed_at = timezone.now()
            transaction.save()

            return Response({
                'success': True,
                'message': 'Transaction status updated',
                'data': TransactionAdminSerializer(transaction).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RefundAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin: list and retrieve Refunds, update status."""
    queryset = Refund.objects.all().select_related('transaction', 'booking', 'requested_by', 'processed_by')
    serializer_class = RefundAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['transaction__transaction_id', 'requested_by__email', 'reason']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update refund status."""
        try:
            refund = self.get_object()
            serializer = RefundStatusUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            refund.status = serializer.validated_data['status']
            if 'admin_notes' in serializer.validated_data:
                refund.admin_notes = serializer.validated_data['admin_notes']
            if 'gateway_refund_id' in serializer.validated_data:
                refund.gateway_refund_id = serializer.validated_data['gateway_refund_id']
            if refund.status in ('completed', 'rejected') and not refund.processed_at:
                refund.processed_at = timezone.now()
                refund.processed_by = request.user
            refund.save()

            return Response({
                'success': True,
                'message': 'Refund status updated',
                'data': RefundAdminSerializer(refund).data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
