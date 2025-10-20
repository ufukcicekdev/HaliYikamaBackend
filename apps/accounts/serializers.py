from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Address, PaymentMethod

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User profile serializer."""
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone',
            'user_type', 'email_verified', 'phone_verified',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'email_verified', 'phone_verified', 'created_at', 'updated_at')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer with password validation."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer."""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class AddressSerializer(serializers.ModelSerializer):
    """Address serializer."""
    
    district_name = serializers.CharField(source='district.name_en', read_only=True)
    
    class Meta:
        model = Address
        fields = (
            'id', 'title', 'district', 'district_name', 'full_address',
            'postal_code', 'building_no', 'apartment_no', 'floor',
            'is_default', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method serializer (read-only for security)."""
    
    class Meta:
        model = PaymentMethod
        fields = (
            'id', 'payment_type', 'card_brand', 'last_four_digits',
            'cardholder_name', 'expiry_month', 'expiry_year',
            'is_default', 'is_active', 'created_at'
        )
        read_only_fields = fields  # All fields read-only for security
