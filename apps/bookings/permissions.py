from rest_framework import permissions


class IsBookingOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of a booking or admins to access/modify it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access all bookings
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
        
        # Users can only access their own bookings
        return obj.user == request.user
