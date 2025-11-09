from rest_framework import serializers
from .models import WeatherData, WeatherAlert


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = ['id', 'latitude', 'longitude', 'temperature', 'humidity', 
                  'rainfall', 'weather_description', 'fetched_at']


class WeatherAlertSerializer(serializers.ModelSerializer):
    weather_data = WeatherDataSerializer(read_only=True)
    
    class Meta:
        model = WeatherAlert
        fields = ['id', 'disease_name', 'crop_name', 'alert_message', 
                  'is_read', 'created_at', 'weather_data']

