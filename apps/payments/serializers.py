from rest_framework import serializers
from .models import Transaction, Refund


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer."""
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'transaction_id', 'booking', 'payment_gateway',
            'amount', 'currency', 'status', 'error_message',
            'created_at', 'completed_at'
        )
        read_only_fields = fields


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer."""
    
    class Meta:
        model = Refund
        fields = (
            'id', 'transaction', 'booking', 'amount', 'reason',
            'status', 'admin_notes', 'created_at', 'processed_at'
        )
        read_only_fields = ('id', 'created_at', 'processed_at')


class PaymentInitiateSerializer(serializers.Serializer):
    """Initiate payment serializer."""
    
    booking_id = serializers.UUIDField()
    payment_method_id = serializers.IntegerField(required=False, allow_null=True)
    save_card = serializers.BooleanField(default=False)
    
    # Card details (if not using saved payment method)
    card_number = serializers.CharField(required=False)
    card_holder = serializers.CharField(required=False)
    expiry_month = serializers.CharField(required=False)
    expiry_year = serializers.CharField(required=False)
    cvv = serializers.CharField(required=False, write_only=True)
