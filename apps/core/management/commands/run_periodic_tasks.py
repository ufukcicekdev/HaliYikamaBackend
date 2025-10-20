"""
Management command to run periodic tasks.
Run this with cron or a task scheduler:

# Every day at 9 AM - send booking reminders
0 9 * * * cd /path/to/project && source venv/bin/activate && python manage.py run_periodic_tasks --task=send_reminders

# Every 30 minutes - clean expired slots
*/30 * * * * cd /path/to/project && source venv/bin/activate && python manage.py run_periodic_tasks --task=clean_slots
"""
from django.core.management.base import BaseCommand
from apps.notifications.tasks import send_booking_reminders
from apps.bookings.tasks import clean_expired_slots, generate_time_slots
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run periodic background tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['send_reminders', 'clean_slots', 'generate_slots', 'all'],
            default='all',
            help='Which task to run'
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=30,
            help='Days ahead for slot generation'
        )

    def handle(self, *args, **options):
        task = options['task']
        
        try:
            if task == 'send_reminders' or task == 'all':
                self.stdout.write('Running send_booking_reminders...')
                result = send_booking_reminders()
                self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            
            if task == 'clean_slots' or task == 'all':
                self.stdout.write('Running clean_expired_slots...')
                result = clean_expired_slots()
                self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            
            if task == 'generate_slots':
                days = options['days_ahead']
                self.stdout.write(f'Running generate_time_slots (days_ahead={days})...')
                result = generate_time_slots(days_ahead=days)
                self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
                
        except Exception as e:
            logger.error(f'Periodic task error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
            raise
