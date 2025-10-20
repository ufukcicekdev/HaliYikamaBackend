from django.contrib import admin
from .models import Transaction, Refund, WebhookLog


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'user', 'booking', 'amount', 
        'payment_gateway', 'status', 'created_at'
    )
    list_filter = ('status', 'payment_gateway', 'created_at')
    search_fields = ('transaction_id', 'gateway_transaction_id', 'user__email', 'booking__booking_number')
    readonly_fields = ('id', 'transaction_id', 'created_at', 'updated_at', 'gateway_response')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('İşlem Bilgileri', {
            'fields': ('id', 'transaction_id', 'user', 'booking', 'payment_method')
        }),
        ('Ödeme Detayları', {
            'fields': ('payment_gateway', 'gateway_transaction_id', 'amount', 'currency', 'refund_amount')
        }),
        ('Durum', {
            'fields': ('status', 'error_message')
        }),
        ('Gateway Yanıtı', {
            'fields': ('gateway_response',),
            'classes': ('collapse',)
        }),
        ('Meta Veriler', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Zaman Damgaları', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'booking', 'amount', 'status', 'requested_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction__transaction_id', 'booking__booking_number', 'gateway_refund_id')
    readonly_fields = ('created_at', 'processed_at')
    ordering = ('-created_at',)


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ('gateway', 'event_type', 'processed', 'created_at')
    list_filter = ('gateway', 'processed', 'event_type', 'created_at')
    search_fields = ('gateway', 'event_type')
    readonly_fields = ('payload', 'headers', 'created_at', 'processed_at')
    ordering = ('-created_at',)
