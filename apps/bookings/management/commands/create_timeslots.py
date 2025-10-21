from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time
from apps.bookings.models import TimeSlot


class Command(BaseCommand):
    help = 'Create time slots for the next 90 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to create slots for (default: 90)'
        )
        parser.add_argument(
            '--capacity',
            type=int,
            default=5,
            help='Maximum capacity per slot (default: 5)'
        )

    def handle(self, *args, **options):
        days = options['days']
        max_capacity = options['capacity']
        
        # Define time slots (9 AM to 6 PM, 2-hour intervals)
        time_slots = [
            (time(9, 0), time(11, 0)),   # 09:00 - 11:00
            (time(11, 0), time(13, 0)),  # 11:00 - 13:00
            (time(13, 0), time(15, 0)),  # 13:00 - 15:00
            (time(15, 0), time(17, 0)),  # 15:00 - 17:00
            (time(17, 0), time(19, 0)),  # 17:00 - 19:00
        ]
        
        start_date = timezone.now().date()
        created_count = 0
        skipped_count = 0
        
        self.stdout.write(self.style.SUCCESS(f'Creating time slots for the next {days} days...'))
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip Sundays (weekday 6)
            if current_date.weekday() == 6:
                continue
            
            for start_time, end_time in time_slots:
                # Check if slot already exists
                existing = TimeSlot.objects.filter(
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new slot
                TimeSlot.objects.create(
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    max_capacity=max_capacity,
                    current_bookings=0,
                    is_available=True
                )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} time slots, skipped {skipped_count} existing slots'
            )
        )
