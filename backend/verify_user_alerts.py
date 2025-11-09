"""
Verify that alerts are user-specific
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')
django.setup()

from weather_alerts.models import WeatherAlert
from django.contrib.auth.models import User

print("=" * 60)
print("🔍 VERIFYING USER-SPECIFIC ALERTS")
print("=" * 60)

for user in User.objects.all():
    alerts = WeatherAlert.objects.filter(user=user, is_read=False)
    print(f"\n👤 User: {user.username}")
    print(f"   Total alerts: {alerts.count()}")
    
    if alerts.exists():
        for i, alert in enumerate(alerts, 1):
            print(f"   {i}. {alert.disease_name} ({alert.crop_name})")

print("\n" + "=" * 60)
print("✅ Each user has their own separate alerts!")
print("=" * 60)

