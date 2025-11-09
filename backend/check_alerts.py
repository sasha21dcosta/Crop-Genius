"""
Quick script to check if weather alerts exist in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')
django.setup()

from weather_alerts.models import WeatherAlert, WeatherData
from django.contrib.auth.models import User

print("=" * 60)
print("🔍 CHECKING WEATHER ALERTS IN DATABASE")
print("=" * 60)

# Check users
users = User.objects.all()
print(f"\n👤 Total users: {users.count()}")

# Check weather data
weather_data = WeatherData.objects.all()
print(f"🌤️  Weather data entries: {weather_data.count()}")
if weather_data.exists():
    latest = weather_data.first()
    print(f"   Latest: {latest.temperature}°C, {latest.humidity}% humidity, {latest.rainfall}mm rain")

# Check alerts
alerts = WeatherAlert.objects.all()
print(f"\n⚠️  Total alerts: {alerts.count()}")
print(f"📬 Unread alerts: {alerts.filter(is_read=False).count()}")

if alerts.exists():
    print("\n" + "=" * 60)
    print("ALERT DETAILS:")
    print("=" * 60)
    for alert in alerts[:5]:  # Show first 5
        print(f"\n👤 User: {alert.user.username}")
        print(f"🦠 Disease: {alert.disease_name}")
        print(f"🌾 Crop: {alert.crop_name}")
        print(f"📋 Message: {alert.alert_message[:80]}...")
        print(f"📖 Read: {alert.is_read}")
        print(f"📅 Created: {alert.created_at}")
else:
    print("\n❌ No alerts found in database!")
    print("\nTroubleshooting:")
    print("1. Run: python manage.py generate_weather_alerts --force-refresh")
    print("2. Make sure users have crops configured")
    print("3. Check if weather conditions match disease risk patterns")

print("\n" + "=" * 60)

