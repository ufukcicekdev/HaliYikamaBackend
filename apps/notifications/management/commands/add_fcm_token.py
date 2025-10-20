"""
Django management command to add a test FCM device token.
"""
from django.core.management.base import BaseCommand
from apps.notifications.models import FCMDevice
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Add a test FCM device token'

    def add_arguments(self, parser):
        parser.add_argument('token', type=str, help='FCM token to add')
        parser.add_argument('--user-email', type=str, default='admin@haliyikama.com', help='User email')

    def handle(self, *args, **options):
        token = options['token']
        user_email = options['user_email']
        
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {user_email} not found')
            )
            return
        
        device, created = FCMDevice.objects.update_or_create(
            token=token,
            defaults={
                'user': user,
                'device_type': 'web',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ FCM device created for {user.email}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ FCM device updated for {user.email}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Token: {token[:30]}...')
        )
