from django.core.management.base import BaseCommand
from apps.core.models import SiteSettings


class Command(BaseCommand):
    help = 'Create default site settings if none exist'

    def handle(self, *args, **options):
        if SiteSettings.objects.exists():
            self.stdout.write(self.style.WARNING('Site settings already exist'))
            return

        settings = SiteSettings.objects.create(
            site_name='Halı Yıkama',
            site_description='İstanbul\'un en güvenilir halı yıkama hizmeti',
            contact_email='info@haliyikama.com',
            contact_phone='0850 123 45 67',
            contact_address='İstanbul, Türkiye',
            contact_form_recipients='admin@haliyikama.com',
            smtp_host='smtp.gmail.com',
            smtp_port=587,
            smtp_username='your-email@gmail.com',
            smtp_password='your-app-password',
            smtp_use_tls=True,
            smtp_use_ssl=False,
            smtp_from_email='noreply@haliyikama.com',
            smtp_from_name='Halı Yıkama',
            whatsapp_number='905301234567',
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created site settings: {settings.site_name}'))
        self.stdout.write(self.style.WARNING('\nIMPORTANT: Please update SMTP settings in admin panel before using contact form!'))
