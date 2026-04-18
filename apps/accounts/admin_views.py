from rest_framework import viewsets, filters, status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminUserSerializer(drf_serializers.ModelSerializer):
    password = drf_serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone',
            'user_type', 'is_active', 'is_staff', 'is_superuser',
            'email_verified', 'phone_verified',
            'date_joined', 'created_at', 'updated_at',
            'password',
        )
        read_only_fields = ('id', 'date_joined', 'created_at', 'updated_at')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin CRUD for Users."""
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'is_active', 'is_staff', 'email_verified']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['created_at', 'date_joined', 'email']
    ordering = ['-created_at']

    def destroy(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            if user == request.user:
                return Response({
                    'success': False,
                    'error': 'You cannot delete your own account'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.delete()
            return Response({'success': True, 'message': 'User deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle user active status."""
        try:
            user = self.get_object()
            if user == request.user:
                return Response({
                    'success': False,
                    'error': 'You cannot deactivate your own account'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = not user.is_active
            user.save()
            return Response({
                'success': True,
                'message': f'User {"activated" if user.is_active else "deactivated"}',
                'data': AdminUserSerializer(user).data
            })
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
