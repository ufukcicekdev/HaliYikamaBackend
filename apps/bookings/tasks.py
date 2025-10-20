"""Background tasks for bookings."""
from django.utils import timezone
from datetime import timedelta
from .models import TimeSlot
import logging

logger = logging.getLogger(__name__)


def clean_expired_slots():
    """
    Clean up expired time slots that are in the past.
    This runs periodically to keep the database clean.
    """
    yesterday = timezone.now().date() - timedelta(days=1)
    expired_count = TimeSlot.objects.filter(date__lt=yesterday).count()
    
    # Optional: archive instead of delete
    TimeSlot.objects.filter(date__lt=yesterday).delete()
    
    return f"Cleaned {expired_count} expired time slots"


def generate_time_slots(days_ahead=30):
    """
    Generate time slots for the next X days based on working hours.
    This should be run daily to maintain availability.
    """
    from apps.services.models import WorkingHours, Holiday
    from datetime import datetime, time, timedelta
    
    today = timezone.now().date()
    end_date = today + timedelta(days=days_ahead)
    
    # Get all holidays
    holidays = set(Holiday.objects.values_list('date', flat=True))
    
    created_count = 0
    current_date = today
    
    while current_date <= end_date:
        # Skip if holiday
        if current_date in holidays:
            current_date += timedelta(days=1)
            continue
        
        # Get working hours for this weekday
        weekday = current_date.weekday()
        try:
            working_hours = WorkingHours.objects.get(weekday=weekday)
        except WorkingHours.DoesNotExist:
            current_date += timedelta(days=1)
            continue
        
        if not working_hours.is_working_day:
            current_date += timedelta(days=1)
            continue
        
        # Generate slots for this day
        slot_duration = timedelta(minutes=working_hours.slot_duration_minutes)
        current_time = datetime.combine(current_date, working_hours.opening_time)
        end_time = datetime.combine(current_date, working_hours.closing_time)
        
        while current_time < end_time:
            slot_end = current_time + slot_duration
            
            # Create slot if it doesn't exist
            slot, created = TimeSlot.objects.get_or_create(
                date=current_date,
                start_time=current_time.time(),
                defaults={
                    'end_time': slot_end.time(),
                    'max_capacity': working_hours.max_bookings_per_slot,
                }
            )
            
            if created:
                created_count += 1
            
            current_time = slot_end
        
        current_date += timedelta(days=1)
    
    return f"Generated {created_count} new time slots"
