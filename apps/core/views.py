from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import SystemSettings


@api_view(['GET'])
@permission_classes([AllowAny])
def get_notification_sound(request):
    """Get notification sound URL."""
    settings = SystemSettings.get_settings()
    
    if settings.notification_sound:
        sound_url = request.build_absolute_uri(settings.notification_sound.url)
    else:
        sound_url = None
    
    return Response({
        'success': True,
        'data': {
            'sound_url': sound_url
        }
    })
