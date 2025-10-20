import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'send-reminder-emails': {
        'task': 'apps.notifications.tasks.send_booking_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
    },
    'clean-expired-slots': {
        'task': 'apps.bookings.tasks.clean_expired_slots',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
