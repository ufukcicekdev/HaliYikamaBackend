import iyzipay
from django.conf import settings
from django.utils import timezone
from .models import Transaction
from apps.accounts.models import PaymentMethod
from decimal import Decimal


class IyzicoPaymentService:
    """iyzico payment gateway integration."""
    
    def __init__(self):
        self.options = {
            'api_key': settings.IYZICO_API_KEY,
            'secret_key': settings.IYZICO_SECRET_KEY,
            'base_url': settings.IYZICO_BASE_URL
        }
    
    def process_payment(self, booking, user, payment_data, ip_address, user_agent):
        """
        Process payment for a booking.
        Returns: dict with success status and transaction details
        """
        # Create transaction record
        transaction = Transaction.objects.create(
            booking=booking,
            user=user,
            payment_gateway='iyzico',
            amount=booking.total,
            currency=booking.currency,
            status='processing',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        try:
            # Prepare payment request
            payment_request = {
                'locale': 'tr',
                'conversationId': str(transaction.id),
                'price': str(booking.subtotal),
                'paidPrice': str(booking.total),
                'currency': iyzipay.Currency.TRY,
                'installment': '1',
                'basketId': str(booking.id),
                'paymentChannel': iyzipay.PaymentChannel.WEB,
                'paymentGroup': iyzipay.PaymentGroup.PRODUCT,
                'callbackUrl': f"{settings.FRONTEND_URL}/payment/callback",
            }
            
            # Buyer information
            payment_request['buyer'] = {
                'id': str(user.id),
                'name': user.first_name,
                'surname': user.last_name,
                'email': user.email,
                'identityNumber': '11111111111',  # Required by iyzico
                'registrationAddress': booking.pickup_address.full_address,
                'city': booking.pickup_address.district.name_en,
                'country': 'Turkey',
                'ip': ip_address
            }
            
            # Shipping address
            payment_request['shippingAddress'] = {
                'contactName': user.get_full_name(),
                'city': booking.pickup_address.district.name_en,
                'country': 'Turkey',
                'address': booking.pickup_address.full_address,
            }
            
            # Billing address (same as shipping)
            payment_request['billingAddress'] = payment_request['shippingAddress'].copy()
            
            # Basket items
            basket_items = []
            for item in booking.items.all():
                basket_items.append({
                    'id': str(item.id),
                    'name': item.subtype.name_en,
                    'category1': item.subtype.category.name_en,
                    'itemType': iyzipay.BasketItemType.PHYSICAL,
                    'price': str(item.line_total)
                })
            
            payment_request['basketItems'] = basket_items
            
            # Payment card
            if payment_data.get('payment_method_id'):
                # Use saved card
                saved_method = PaymentMethod.objects.get(
                    id=payment_data['payment_method_id'],
                    user=user,
                    is_active=True
                )
                payment_request['paymentCard'] = {
                    'cardToken': saved_method.card_token,
                }
            else:
                # New card
                payment_request['paymentCard'] = {
                    'cardHolderName': payment_data['card_holder'],
                    'cardNumber': payment_data['card_number'],
                    'expireMonth': payment_data['expiry_month'],
                    'expireYear': payment_data['expiry_year'],
                    'cvc': payment_data['cvv'],
                }
            
            # Initialize 3D Secure payment
            payment = iyzipay.ThreedsInitialize().create(payment_request, self.options)
            
            if payment.status == 'success':
                # Store gateway transaction ID
                transaction.gateway_transaction_id = payment.payment_id
                transaction.gateway_response = payment.read().decode('utf-8')
                transaction.save()
                
                # If saving card, tokenize it
                if payment_data.get('save_card') and not payment_data.get('payment_method_id'):
                    self._save_card_token(user, payment_data, payment.card_token)
                
                return {
                    'success': True,
                    'transaction_id': str(transaction.id),
                    'three_ds_url': payment.threeds_html_content  # iyzico returns HTML for 3D Secure
                }
            else:
                transaction.status = 'failed'
                transaction.error_message = payment.error_message
                transaction.save()
                
                return {
                    'success': False,
                    'error': payment.error_message
                }
                
        except Exception as e:
            transaction.status = 'failed'
            transaction.error_message = str(e)
            transaction.save()
            raise
    
    def handle_3ds_callback(self, callback_data):
        """Handle 3D Secure callback."""
        # Verify payment result
        conversation_id = callback_data.get('conversationId')
        
        try:
            transaction = Transaction.objects.get(id=conversation_id)
            
            # Retrieve payment result
            request = {
                'locale': 'tr',
                'conversationId': conversation_id,
                'paymentId': callback_data.get('paymentId')
            }
            
            payment_result = iyzipay.ThreedsPayment().retrieve(request, self.options)
            
            if payment_result.status == 'success':
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.save()
                
                # Update booking status
                booking = transaction.booking
                booking.status = 'confirmed'
                booking.confirmed_at = timezone.now()
                booking.save()
                
                return {
                    'success': True,
                    'booking_id': str(booking.id)
                }
            else:
                transaction.status = 'failed'
                transaction.error_message = payment_result.error_message
                transaction.save()
                
                return {
                    'success': False,
                    'error': payment_result.error_message
                }
                
        except Transaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Transaction not found'
            }
    
    def handle_webhook(self, webhook_data, webhook_log):
        """Handle iyzico webhooks."""
        # iyzico webhook handling implementation
        pass
    
    def _save_card_token(self, user, payment_data, card_token):
        """Save tokenized card for future use."""
        PaymentMethod.objects.create(
            user=user,
            payment_type='card',
            card_token=card_token,
            cardholder_name=payment_data['card_holder'],
            last_four_digits=payment_data['card_number'][-4:],
            expiry_month=payment_data['expiry_month'],
            expiry_year=payment_data['expiry_year'],
            # Card brand detection would go here
        )
