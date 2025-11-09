from django.contrib import admin
from .models import WeatherData, WeatherAlert


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['user', 'temperature', 'humidity', 'rainfall', 'fetched_at']
    list_filter = ['fetched_at']
    search_fields = ['user__username']


@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'disease_name', 'crop_name', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'disease_name']
    search_fields = ['user__username', 'disease_name', 'crop_name']
    actions = ['mark_as_read']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected alerts as read"

