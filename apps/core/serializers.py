from rest_framework import serializers
from .models import ContactFormSubmission, SiteSettings


class ContactFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactFormSubmission
        fields = ['name', 'email', 'phone', 'message']
    
    def validate_email(self, value):
        """Email formatını kontrol et"""
        if not value:
            raise serializers.ValidationError("E-posta adresi gereklidir")
        return value
    
    def validate_message(self, value):
        """Mesaj boş olmamalı"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Mesaj en az 10 karakter olmalıdır")
        return value


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_description', 'contact_email', 
            'contact_phone', 'contact_address', 'facebook_url',
            'instagram_url', 'twitter_url', 'whatsapp_number'
        ]
