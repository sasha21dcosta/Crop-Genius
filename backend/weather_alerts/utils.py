"""
Weather-based disease alert utilities
Fetches weather data and evaluates disease risk based on conditions
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from django.contrib.auth.models import User
from .models import WeatherData, WeatherAlert

logger = logging.getLogger(__name__)


def get_weather(lat: float, lon: float, api_key: Optional[str] = None) -> Dict:
    """
    Fetch real-time weather data from OpenWeatherMap API
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        api_key: OpenWeatherMap API key (optional, will use env var if not provided)
    
    Returns:
        Dictionary containing temperature, humidity, rainfall, and weather description
    """
    api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        logger.warning("No OpenWeatherMap API key provided, using default values")
        return {
            "temperature": 28.0,
            "humidity": 82.0,
            "rainfall": 12.0,
            "description": "Heavy rain - Test mode"
        }
    
    try:
        # Current weather endpoint
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract weather data
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        
        # Rainfall in last 1 hour (if available)
        rainfall = data.get('rain', {}).get('1h', 0.0)
        
        logger.info(f"Weather fetched for ({lat}, {lon}): {temperature}°C, {humidity}% humidity, {rainfall}mm rain")
        
        return {
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "description": description
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        # Return default values on error
        return {
            "temperature": 25.0,
            "humidity": 70.0,
            "rainfall": 0.0,
            "description": "Unknown"
        }


def load_weather_disease_kb() -> List[Dict]:
    """
    Load the weather-disease risk knowledge base from JSON file
    
    Returns:
        List of disease risk condition mappings
    """
    kb_path = Path(__file__).parent / 'weather_disease_kb.json'
    
    try:
        with open(kb_path, 'r') as f:
            kb = json.load(f)
        logger.info(f"Loaded {len(kb)} disease risk patterns from knowledge base")
        return kb
    except Exception as e:
        logger.error(f"Error loading weather disease KB: {e}")
        return []


def evaluate_risk(weather_data: Dict, disease_kb: List[Dict], user_crops: List[str]) -> List[Dict]:
    """
    Evaluate disease risk based on current weather conditions and user's crops
    
    Args:
        weather_data: Dictionary with temperature, humidity, rainfall
        disease_kb: List of disease risk patterns from knowledge base
        user_crops: List of crops the user grows
    
    Returns:
        List of alerts where risk conditions match
    """
    alerts = []
    temp = weather_data['temperature']
    humidity = weather_data['humidity']
    rainfall = weather_data['rainfall']
    
    logger.info(f"Evaluating risk for crops: {user_crops}")
    logger.info(f"Weather conditions: {temp}°C, {humidity}% humidity, {rainfall}mm rain")
    
    for disease in disease_kb:
        crop = disease['crop_name'].lower()
        
        # Check if disease applies to any of user's crops
        if not any(user_crop.lower() == crop for user_crop in user_crops):
            continue
        
        conditions = disease['risk_conditions']
        is_risky = True
        
        # Check temperature conditions
        if 'min_temp' in conditions and temp < conditions['min_temp']:
            is_risky = False
        if 'max_temp' in conditions and temp > conditions['max_temp']:
            is_risky = False
        
        # Check humidity conditions
        if 'min_humidity' in conditions and humidity < conditions['min_humidity']:
            is_risky = False
        if 'max_humidity' in conditions and humidity > conditions['max_humidity']:
            is_risky = False
        
        # Check rainfall conditions
        if 'min_rainfall' in conditions and rainfall < conditions['min_rainfall']:
            is_risky = False
        if 'max_rainfall' in conditions and rainfall > conditions['max_rainfall']:
            is_risky = False
        
        if is_risky:
            alerts.append({
                'disease_name': disease['disease_name'],
                'crop_name': disease['crop_name'],
                'alert_message': conditions['alert']
            })
            logger.info(f"⚠️ Risk detected: {disease['disease_name']} on {disease['crop_name']}")
    
    return alerts


def get_or_fetch_weather(user: User, force_refresh: bool = False) -> Tuple[WeatherData, bool]:
    """
    Get cached weather data or fetch new data if cache is old
    
    Args:
        user: User object
        force_refresh: Force fetch new weather data
    
    Returns:
        Tuple of (WeatherData object, is_new_data boolean)
    """
    # Check if user has profile with location
    if not hasattr(user, 'profile'):
        logger.warning(f"User {user.username} has no profile")
        # Return default weather data
        return None, False
    
    # For now, we'll use IP-based location or default coordinates
    # In production, you'd store lat/lon in user profile
    lat, lon = get_location_for_user(user)
    
    # Check for recent weather data (less than 1 hour old)
    if not force_refresh:
        recent_weather = WeatherData.objects.filter(
            user=user,
            fetched_at__gte=datetime.now() - timedelta(hours=1)
        ).first()
        
        if recent_weather:
            logger.info(f"Using cached weather data for {user.username}")
            return recent_weather, False
    
    # Fetch new weather data
    logger.info(f"Fetching new weather data for {user.username}")
    weather = get_weather(lat, lon)
    
    # Save to database
    weather_obj = WeatherData.objects.create(
        user=user,
        latitude=lat,
        longitude=lon,
        temperature=weather['temperature'],
        humidity=weather['humidity'],
        rainfall=weather['rainfall'],
        weather_description=weather['description']
    )
    
    return weather_obj, True


def get_location_for_user(user: User) -> Tuple[float, float]:
    """
    Get location coordinates for a user
    
    For now, returns default India coordinates
    In production, you'd store lat/lon in user profile or get from IP
    
    Args:
        user: User object
    
    Returns:
        Tuple of (latitude, longitude)
    """
    # TODO: Add lat/lon fields to UserProfile model
    # For now, return default coordinates (center of India)
    return 20.5937, 78.9629


def generate_alerts_for_user(user: User, force_refresh: bool = False) -> int:
    """
    Generate weather-based disease alerts for a user
    
    Args:
        user: User object
        force_refresh: Force fetch new weather data
    
    Returns:
        Number of new alerts generated
    """
    # Get user's crops
    if not hasattr(user, 'profile'):
        logger.warning(f"User {user.username} has no profile, skipping alerts")
        return 0
    
    user_crops = user.profile.get_crops_list()
    if not user_crops:
        logger.info(f"User {user.username} has no crops configured, skipping alerts")
        return 0
    
    # Get weather data
    weather_data_obj, is_new = get_or_fetch_weather(user, force_refresh)
    if not weather_data_obj:
        return 0
    
    weather_dict = {
        'temperature': weather_data_obj.temperature,
        'humidity': weather_data_obj.humidity,
        'rainfall': weather_data_obj.rainfall,
        'description': weather_data_obj.weather_description
    }
    
    # Load disease KB and evaluate risks
    disease_kb = load_weather_disease_kb()
    risk_alerts = evaluate_risk(weather_dict, disease_kb, user_crops)
    
    # Delete old alerts from today to avoid duplicates
    WeatherAlert.objects.filter(
        user=user,
        created_at__date=datetime.now().date()
    ).delete()
    
    # Create new alerts
    alerts_created = 0
    for alert in risk_alerts:
        WeatherAlert.objects.create(
            user=user,
            disease_name=alert['disease_name'],
            crop_name=alert['crop_name'],
            alert_message=alert['alert_message'],
            weather_data=weather_data_obj
        )
        alerts_created += 1
    
    logger.info(f"Generated {alerts_created} alerts for user {user.username}")
    return alerts_created


def generate_alerts_for_all_users(force_refresh: bool = False) -> Dict[str, int]:
    """
    Generate alerts for all users with profiles and crops
    
    Args:
        force_refresh: Force fetch new weather data for all users
    
    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_users': 0,
        'users_processed': 0,
        'total_alerts': 0
    }
    
    # Get all users with profiles and crops
    from agri_app.models import UserProfile
    
    users_with_crops = User.objects.filter(
        profile__isnull=False
    ).exclude(profile__crops='')
    
    stats['total_users'] = users_with_crops.count()
    
    for user in users_with_crops:
        try:
            alerts_count = generate_alerts_for_user(user, force_refresh)
            stats['users_processed'] += 1
            stats['total_alerts'] += alerts_count
        except Exception as e:
            logger.error(f"Error generating alerts for {user.username}: {e}")
    
    logger.info(f"Alert generation complete: {stats}")
    return stats

