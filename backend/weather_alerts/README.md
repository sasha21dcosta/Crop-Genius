# Weather-Based Disease Alert System

A Django app that provides real-time weather-based disease risk alerts to farmers.

## 🎯 What It Does

- Fetches current weather data from OpenWeatherMap API
- Compares weather against disease risk patterns
- Generates alerts when conditions match risk criteria
- Displays beautiful alert cards on Flutter home page
- Allows users to dismiss alerts

## 📦 Installation

```bash
# Run migrations
python manage.py migrate

# Generate alerts
python manage.py generate_weather_alerts
```

## 📖 Documentation

- **Quick Setup**: See `../WEATHER_ALERTS_SETUP.md` for step-by-step setup
- **Full Guide**: See `../WEATHER_ALERTS_GUIDE.md` for complete documentation

## 🔌 API Endpoints

- `GET /api/weather/alerts/` - Get all alerts
- `GET /api/weather/alerts/active/` - Get unread alerts
- `POST /api/weather/alerts/{id}/read/` - Mark alert as read
- `POST /api/weather/alerts/refresh/` - Refresh alerts

## 💻 Management Command

```bash
python manage.py generate_weather_alerts [--force-refresh]
```

## 📱 Flutter Integration

Alerts automatically display on the home page above "Our Services" section.

## 🗂️ Files Structure

```
weather_alerts/
├── models.py                      # Database models
├── views.py                       # API endpoints
├── utils.py                       # Core logic
├── serializers.py                 # DRF serializers
├── admin.py                       # Admin interface
├── urls.py                        # URL routing
├── weather_disease_kb.json        # Disease risk knowledge base
└── management/commands/
    └── generate_weather_alerts.py # Management command
```

## 🌟 Features

✅ 20+ pre-configured disease risk patterns  
✅ Automatic weather data caching (1 hour)  
✅ User-specific alerts based on their crops  
✅ Beautiful Flutter UI with dismissible cards  
✅ Admin interface for alert management  
✅ RESTful API endpoints  
✅ Scheduled execution support  

## 🚀 Quick Start

1. Set OpenWeatherMap API key: `export OPENWEATHER_API_KEY="your_key"`
2. Run migrations: `python manage.py migrate`
3. Generate alerts: `python manage.py generate_weather_alerts`
4. View in app or admin panel!

---

**Built for CropGenius Agricultural Platform**

