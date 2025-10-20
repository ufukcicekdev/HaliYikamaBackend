from django.contrib import admin
from .models import District, Category, SubType, Pricing, WorkingHours, Holiday, BookingSettings


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'delivery_fee', 'is_active', 'order_priority')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order_priority', 'name')
    
    # Turkish Labels
    verbose_name = 'Bölge'
    verbose_name_plural = 'Bölgeler'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'pricing_type', 'is_active', 'order_priority', 'requires_time_selection', 'requires_pickup_delivery')
    list_filter = ('is_active', 'pricing_type', 'requires_time_selection', 'requires_pickup_delivery')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order_priority', 'name')
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'slug', 'description', 'icon', 'image', 'pricing_type')
        }),
        ('Zamanlama Ayarları', {
            'fields': ('requires_time_selection', 'requires_pickup_delivery', 'min_days_between_pickup_delivery')
        }),
        ('Görünürlük', {
            'fields': ('is_active', 'order_priority')
        }),
    )


class PricingInline(admin.TabularInline):
    model = Pricing
    extra = 1


@admin.register(SubType)
class SubTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'is_active', 'order_priority')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('category', 'order_priority', 'name')
    inlines = [PricingInline]


@admin.register(Pricing)
class PricingAdmin(admin.ModelAdmin):
    list_display = ('subtype', 'base_price', 'currency', 'discount_percentage', 'is_active', 'valid_from', 'valid_until')
    list_filter = ('is_active', 'currency', 'subtype__category')
    search_fields = ('subtype__name',)
    ordering = ('-created_at',)


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('get_weekday_turkish', 'is_working_day', 'opening_time', 'closing_time', 'slot_duration_minutes', 'max_bookings_per_slot')
    list_filter = ('is_working_day',)
    ordering = ('weekday',)
    
    def get_weekday_turkish(self, obj):
        days = {
            0: 'Pazartesi',
            1: 'Salı',
            2: 'Çarşamba',
            3: 'Perşembe',
            4: 'Cuma',
            5: 'Cumartesi',
            6: 'Pazar',
        }
        return days.get(obj.weekday, '')
    get_weekday_turkish.short_description = 'Gün'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')
    search_fields = ('name',)
    ordering = ('-date',)


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('İptal Kuralları', {
            'fields': ('min_cancellation_notice_hours', 'min_reschedule_notice_hours')
        }),
        ('Cezalar', {
            'fields': ('cancellation_fee_percentage', 'late_cancellation_fee_percentage')
        }),
        ('Varsayılan Hizmet Saatleri', {
            'fields': ('default_service_start_time', 'default_service_end_time')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance (singleton)
        return not BookingSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False
