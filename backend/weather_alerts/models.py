from django.db import models
from django.contrib.auth.models import User


class WeatherData(models.Model):
    """Cache for weather data to reduce API calls"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_data')
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature = models.FloatField()  # Celsius
    humidity = models.FloatField()  # Percentage
    rainfall = models.FloatField()  # mm
    weather_description = models.CharField(max_length=255)
    fetched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fetched_at']
        verbose_name_plural = 'Weather Data'
    
    def __str__(self):
        return f"Weather for {self.user.username} at ({self.latitude}, {self.longitude}) - {self.fetched_at}"


class WeatherAlert(models.Model):
    """Store disease alerts based on weather conditions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_alerts')
    disease_name = models.CharField(max_length=255)
    crop_name = models.CharField(max_length=255)
    alert_message = models.TextField()
    weather_data = models.ForeignKey(WeatherData, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert for {self.user.username}: {self.disease_name} on {self.crop_name}"

