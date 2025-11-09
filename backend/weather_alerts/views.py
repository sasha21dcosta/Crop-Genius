from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import WeatherAlert, WeatherData
from .serializers import WeatherAlertSerializer, WeatherDataSerializer
from .utils import generate_alerts_for_user, generate_alerts_for_all_users
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_alerts(request):
    """
    Get all weather alerts for the authenticated user
    Returns unread alerts first
    """
    try:
        # Get all alerts for the user, unread first
        alerts = WeatherAlert.objects.filter(user=request.user).order_by('is_read', '-created_at')
        
        serializer = WeatherAlertSerializer(alerts, many=True)
        
        return Response({
            'success': True,
            'count': alerts.count(),
            'unread_count': alerts.filter(is_read=False).count(),
            'alerts': serializer.data
        })
    
    except Exception as e:
        logger.error(f"Error fetching alerts for user {request.user.username}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_alerts(request):
    """
    Get only unread/active alerts for the authenticated user
    """
    try:
        alerts = WeatherAlert.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')
        
        serializer = WeatherAlertSerializer(alerts, many=True)
        
        return Response({
            'success': True,
            'count': alerts.count(),
            'alerts': serializer.data
        })
    
    except Exception as e:
        logger.error(f"Error fetching active alerts: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_read(request, alert_id):
    """
    Mark a specific alert as read
    """
    try:
        alert = WeatherAlert.objects.get(id=alert_id, user=request.user)
        alert.is_read = True
        alert.save()
        
        return Response({
            'success': True,
            'message': 'Alert marked as read'
        })
    
    except WeatherAlert.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Alert not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error marking alert as read: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_alerts_read(request):
    """
    Mark all alerts as read for the authenticated user
    """
    try:
        count = WeatherAlert.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'message': f'Marked {count} alerts as read'
        })
    
    except Exception as e:
        logger.error(f"Error marking all alerts as read: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_alerts(request):
    """
    Force refresh weather data and regenerate alerts for the user
    """
    try:
        alerts_count = generate_alerts_for_user(request.user, force_refresh=True)
        
        return Response({
            'success': True,
            'message': f'Generated {alerts_count} new alerts',
            'alerts_count': alerts_count
        })
    
    except Exception as e:
        logger.error(f"Error refreshing alerts: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_weather(request):
    """
    Get current weather data for the authenticated user
    """
    try:
        # Get most recent weather data
        weather = WeatherData.objects.filter(user=request.user).first()
        
        if not weather:
            return Response({
                'success': False,
                'message': 'No weather data available. Try refreshing alerts.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = WeatherDataSerializer(weather)
        
        return Response({
            'success': True,
            'weather': serializer.data
        })
    
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_alerts_manual(request):
    """
    Admin endpoint to manually trigger alert generation for all users
    Requires staff/admin permissions in production
    """
    # TODO: Add permission check for admin only
    # if not request.user.is_staff:
    #     return Response({'error': 'Admin access required'}, status=403)
    
    try:
        force_refresh = request.data.get('force_refresh', False)
        stats = generate_alerts_for_all_users(force_refresh)
        
        return Response({
            'success': True,
            'message': 'Alert generation completed',
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error in manual alert generation: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

