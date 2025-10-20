from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email as username."""
    
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('technician', 'Technician'),
    ]
    
    username = None
    email = models.EmailField(unique=True, verbose_name="E-posta")
    phone = PhoneNumberField(blank=True, null=True, verbose_name="Telefon")
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer', verbose_name="Kullanıcı Tipi")
    email_verified = models.BooleanField(default=False, verbose_name="E-posta Doğrulandı")
    phone_verified = models.BooleanField(default=False, verbose_name="Telefon Doğrulandı")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Address(models.Model):
    """User saved addresses."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name="Kullanıcı")
    title = models.CharField(max_length=100, help_text='e.g., Home, Office', verbose_name="Adres Başlığı")
    district = models.ForeignKey('services.District', on_delete=models.PROTECT, verbose_name="Bölge")
    full_address = models.TextField(verbose_name="Tam Adres")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="Posta Kodu")
    building_no = models.CharField(max_length=20, blank=True, verbose_name="Bina No")
    apartment_no = models.CharField(max_length=20, blank=True, verbose_name="Daire No")
    floor = models.CharField(max_length=10, blank=True, verbose_name="Kat")
    is_default = models.BooleanField(default=False, verbose_name="Varsayılan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Adres'
        verbose_name_plural = 'Adresler'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default address per user
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    """Stored payment methods with tokenization."""
    
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Credit/Debit Card'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods', verbose_name="Kullanıcı")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='card', verbose_name="Ödeme Tipi")
    card_token = models.CharField(max_length=255, unique=True, verbose_name="Kart Token")  # Tokenized card info
    card_brand = models.CharField(max_length=50, blank=True, verbose_name="Kart Markası")  # Visa, MasterCard, etc.
    last_four_digits = models.CharField(max_length=4, verbose_name="Son 4 Hane")
    cardholder_name = models.CharField(max_length=100, verbose_name="Kart Sahibi Adı")
    expiry_month = models.CharField(max_length=2, verbose_name="Son Kullanma Ay")
    expiry_year = models.CharField(max_length=4, verbose_name="Son Kullanma Yıl")
    is_default = models.BooleanField(default=False, verbose_name="Varsayılan")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = 'Ödeme Yöntemi'
        verbose_name_plural = 'Ödeme Yöntemleri'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.card_brand} **** {self.last_four_digits}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default payment method per user
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
