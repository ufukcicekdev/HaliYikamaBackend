"""
Firebase Cloud Messaging (FCM) service for sending push notifications.
"""
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


class FCMService:
    """Service for sending FCM push notifications."""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK."""
        if cls._initialized:
            return
        
        try:
            # Get credentials from Django settings (loaded from environment variables)
            project_id = settings.FIREBASE_PROJECT_ID
            private_key = settings.FIREBASE_PRIVATE_KEY
            client_email = settings.FIREBASE_CLIENT_EMAIL
            
            if project_id and private_key and client_email:
                # Initialize from environment variables
                cred_dict = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key": private_key.replace('\\n', '\n'),  # Fix escaped newlines
                    "client_email": client_email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                logger.info('Firebase Admin SDK initialized successfully')
            else:
                logger.warning('Firebase credentials not found in settings. Push notifications disabled.')
            
        except Exception as e:
            logger.error(f'Error initializing Firebase Admin SDK: {e}')
    
    @classmethod
    def send_notification(cls, token, title, body, data=None):
        """
        Send a push notification to a single device.
        
        Args:
            token (str): FCM device token
            title (str): Notification title
            body (str): Notification body
            data (dict): Optional data payload
        
        Returns:
            str: Message ID if successful, None otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._initialized:
            logger.warning('FCM not initialized. Cannot send notification.')
            return None
        
        try:
            # Prepare data payload (convert all values to strings)
            data_payload = {}
            if data:
                for key, value in data.items():
                    data_payload[key] = str(value)
            
            # Add title and body to data for background handling
            data_payload['title'] = title
            data_payload['body'] = body
            
            # Get the URL from data or use default
            notification_url = data.get('url', '/admin/dashboard') if data else '/admin/dashboard'
            
            # Build webpush config - only add link if in production (HTTPS)
            webpush_notification = messaging.WebpushNotification(
                icon='/notification-icon.png',
                badge='/badge-icon.png',
                require_interaction=True,
                vibrate=[200, 100, 200],
            )
            
            # Only set FCM options with link if we have HTTPS URL
            fcm_options = None
            if hasattr(settings, 'SITE_URL') and settings.SITE_URL.startswith('https'):
                fcm_options = messaging.WebpushFCMOptions(
                    link=f"{settings.SITE_URL}{notification_url}"
                )
            
            webpush_config = messaging.WebpushConfig(
                notification=webpush_notification,
                fcm_options=fcm_options,
                # Store URL in data instead for local development
                data={'url': notification_url}
            )
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data_payload,
                token=token,
                webpush=webpush_config,
                # Android specific config
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        click_action='FLUTTER_NOTIFICATION_CLICK',
                    )
                ),
                # APNs (iOS) specific config
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f'Successfully sent message: {response}')
            return response
            
        except Exception as e:
            logger.error(f'Error sending FCM notification: {e}')
            return None
    
    @classmethod
    def send_multicast(cls, tokens, title, body, data=None):
        """
        Send a push notification to multiple devices.
        
        Args:
            tokens (list): List of FCM device tokens
            title (str): Notification title
            body (str): Notification body
            data (dict): Optional data payload
        
        Returns:
            dict: Results with success and failure counts
        """
        if not cls._initialized:
            cls.initialize()
        
        if not cls._initialized:
            logger.warning('FCM not initialized. Cannot send notifications.')
            return None
        
        if not tokens:
            logger.warning('No tokens provided for multicast notification.')
            return None
        
        try:
            success_count = 0
            failure_count = 0
            errors = []
            
            # Send to each token individually
            for token in tokens:
                try:
                    result = cls.send_notification(token, title, body, data)
                    if result:
                        success_count += 1
                    else:
                        failure_count += 1
                        errors.append(f'Failed to send to token: {token[:20]}...')
                except Exception as e:
                    failure_count += 1
                    errors.append(f'Error sending to token: {str(e)}')
                    logger.error(f'Error sending to token {token[:20]}...: {e}')
            
            logger.info(f'Successfully sent {success_count} messages, {failure_count} failed')
            
            if errors:
                for error in errors[:5]:  # Log first 5 errors
                    logger.warning(error)
            
            return {
                'success_count': success_count,
                'failure_count': failure_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f'Error sending FCM multicast: {e}')
            return None
    
    @classmethod
    def send_to_admin_users(cls, title, body, data=None):
        """
        Send push notification to all admin users.
        
        Args:
            title (str): Notification title
            body (str): Notification body
            data (dict): Optional data payload
        
        Returns:
            BatchResponse: Batch response object
        """
        from apps.notifications.models import FCMDevice
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Get all admin users
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        # Get active FCM tokens for admin users
        tokens = list(
            FCMDevice.objects.filter(
                user__in=admin_users,
                is_active=True
            ).values_list('token', flat=True)
        )
        
        if not tokens:
            logger.warning('No active FCM tokens found for admin users.')
            return None
        
        logger.info(f'Sending notification to {len(tokens)} admin devices')
        return cls.send_multicast(tokens, title, body, data)
    
    @classmethod
    def send_to_user(cls, user, title, body, data=None):
        """
        Send push notification to a specific user.
        
        Args:
            user: User instance
            title (str): Notification title
            body (str): Notification body
            data (dict): Optional data payload
        
        Returns:
            dict: Results with success and failure counts
        """
        from apps.notifications.models import FCMDevice
        
        # Get active FCM tokens for this user
        tokens = list(
            FCMDevice.objects.filter(
                user=user,
                is_active=True
            ).values_list('token', flat=True)
        )
        
        if not tokens:
            logger.warning(f'No active FCM tokens found for user {user.email}.')
            return None
        
        logger.info(f'Sending notification to {len(tokens)} devices for user {user.email}')
        return cls.send_multicast(tokens, title, body, data)
