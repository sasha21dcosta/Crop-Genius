from django.urls import path
from . import views

app_name = 'weather_alerts'

urlpatterns = [
    # Get alerts
    path('alerts/', views.get_user_alerts, name='user_alerts'),
    path('alerts/active/', views.get_active_alerts, name='active_alerts'),
    
    # Mark as read
    path('alerts/<int:alert_id>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('alerts/mark-all-read/', views.mark_all_alerts_read, name='mark_all_read'),
    
    # Refresh alerts
    path('alerts/refresh/', views.refresh_alerts, name='refresh_alerts'),
    
    # Weather data
    path('weather/', views.get_current_weather, name='current_weather'),
    
    # Manual generation (admin)
    path('alerts/generate/', views.generate_alerts_manual, name='generate_alerts'),
]

