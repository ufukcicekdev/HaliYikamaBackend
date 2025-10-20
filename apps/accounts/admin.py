from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Address, PaymentMethod


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('first_name', 'last_name', 'phone', 'user_type')}),
        ('Doğrulama', {'fields': ('email_verified', 'phone_verified')}),
        ('Yetkiler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Önemli Tarihler', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'email_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type', 'email_verified')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'district', 'is_default', 'created_at')
    list_filter = ('is_default', 'district')
    search_fields = ('user__email', 'title', 'full_address')
    ordering = ('-created_at',)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_brand', 'last_four_digits', 'is_default', 'is_active', 'created_at')
    list_filter = ('is_default', 'is_active', 'card_brand')
    search_fields = ('user__email', 'cardholder_name', 'last_four_digits')
    ordering = ('-created_at',)
    readonly_fields = ('card_token',)
