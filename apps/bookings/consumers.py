from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime, timedelta


class TimeSlotConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time time slot availability."""
    
    async def connect(self):
        # Join time slot updates group
        await self.channel_layer.group_add(
            "timeslot_updates",
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave time slot updates group
        await self.channel_layer.group_discard(
            "timeslot_updates",
            self.channel_name
        )
    
    async def receive_json(self, content):
        """
        Handle incoming WebSocket messages.
        Expected format: {"action": "subscribe", "date": "2024-01-15"}
        """
        action = content.get('action')
        
        if action == 'subscribe':
            date_str = content.get('date')
            if date_str:
                # Send current availability for the requested date
                slots = await self.get_available_slots(date_str)
                await self.send_json({
                    'type': 'slots_update',
                    'date': date_str,
                    'slots': slots
                })
    
    async def timeslot_update(self, event):
        """
        Handle timeslot update events from the channel layer.
        """
        await self.send_json({
            'type': 'slots_update',
            'date': event['date'],
            'slot_id': event['slot_id'],
            'is_available': event['is_available'],
            'current_bookings': event['current_bookings'],
            'max_capacity': event['max_capacity']
        })
    
    @database_sync_to_async
    def get_available_slots(self, date_str):
        """Get available time slots for a specific date."""
        from .models import TimeSlot
        from .serializers import TimeSlotSerializer
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slots = TimeSlot.objects.filter(date=date, is_available=True).order_by('start_time')
            return [TimeSlotSerializer(slot).data for slot in slots]
        except Exception as e:
            return []
