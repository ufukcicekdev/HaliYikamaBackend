from django.contrib import admin
from .models import Booking, BookingItem, TimeSlot, BookingStatusHistory


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    readonly_fields = ('line_total',)


class BookingStatusHistoryInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'created_at')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_number', 'user', 'status', 'pickup_date', 
        'total', 'assigned_technician', 'created_at'
    )
    list_filter = ('status', 'pickup_date', 'created_at')
    search_fields = ('booking_number', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('id', 'booking_number', 'created_at', 'updated_at', 'total')
    ordering = ('-created_at',)
    inlines = [BookingItemInline, BookingStatusHistoryInline]
    
    fieldsets = (
        ('Rezervasyon Bilgileri', {
            'fields': ('id', 'booking_number', 'user', 'status')
        }),
        ('Konum', {
            'fields': ('pickup_address', 'delivery_address')
        }),
        ('Zamanlama', {
            'fields': (
                'pickup_date', 'pickup_time_slot', 
                'delivery_date', 'delivery_time_slot',
                'assigned_technician'
            )
        }),
        ('Fiyatlandırma', {
            'fields': ('subtotal', 'delivery_fee', 'discount', 'total', 'currency')
        }),
        ('Notlar', {
            'fields': ('customer_notes', 'admin_notes', 'cancellation_reason')
        }),
        ('Zaman Damgaları', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at')
        }),
    )


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ('booking', 'subtype', 'quantity', 'unit_price', 'line_total')
    list_filter = ('subtype__category',)
    search_fields = ('booking__booking_number', 'subtype__name_en')
    readonly_fields = ('line_total',)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_time', 'end_time', 'current_bookings', 'max_capacity', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('date',)
    ordering = ('-date', 'start_time')


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('booking', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at')
    search_fields = ('booking__booking_number',)
    readonly_fields = ('booking', 'old_status', 'new_status', 'changed_by', 'created_at')
    ordering = ('-created_at',)
