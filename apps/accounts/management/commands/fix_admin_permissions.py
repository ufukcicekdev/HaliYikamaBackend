"""
Django management command to ensure admin user has correct permissions.
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Ensure admin users have proper staff and superuser status'

    def handle(self, *args, **options):
        # Find all users with user_type='admin'
        admin_users = User.objects.filter(user_type='admin')
        
        updated_count = 0
        for user in admin_users:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated user: {user.email} - is_staff and is_superuser set to True')
                )
        
        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All admin users already have correct permissions')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} admin user(s)')
            )
