# 🌦️ Weather-Based Disease Alert System

A Django-based intelligent alert system that monitors weather conditions and warns farmers about potential crop disease risks.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Management Commands](#management-commands)
- [Frontend Integration](#frontend-integration)
- [Knowledge Base](#knowledge-base)

---

## 🎯 Overview

The Weather-Based Disease Alert System fetches real-time weather data and compares it against a knowledge base of disease risk conditions. When weather conditions match disease risk patterns for crops a farmer is growing, the system generates alerts to help prevent crop losses.

### How It Works

1. **Weather Fetching**: Gets current weather data (temperature, humidity, rainfall) from OpenWeatherMap API
2. **Risk Evaluation**: Compares weather conditions against disease risk patterns in the knowledge base
3. **Alert Generation**: Creates alerts for crops that match risk conditions
4. **User Notification**: Displays alerts on the Flutter frontend homepage

---

## ✨ Features

- ✅ Real-time weather data fetching from OpenWeatherMap
- ✅ Weather data caching to reduce API calls (1-hour cache)
- ✅ 20+ pre-configured disease risk patterns for common crops
- ✅ User-specific alerts based on crops they grow
- ✅ Beautiful Flutter UI with dismissible alert cards
- ✅ Mark alerts as read/unread functionality
- ✅ Django management command for scheduled execution
- ✅ RESTful API endpoints
- ✅ Admin interface for managing alerts

---

## 🏗️ Architecture

```
weather_alerts/
├── models.py              # WeatherData & WeatherAlert models
├── utils.py               # Core logic (weather fetching, risk evaluation)
├── views.py               # API endpoints
├── serializers.py         # DRF serializers
├── admin.py              # Django admin configuration
├── urls.py               # URL routing
├── weather_disease_kb.json   # Disease risk knowledge base
└── management/
    └── commands/
        └── generate_weather_alerts.py   # Scheduled command
```

---

## 📦 Installation

### 1. Database Migration

Run migrations to create the database tables:

```bash
cd backend
python manage.py makemigrations weather_alerts
python manage.py migrate
```

### 2. Verify Installation

Check that the app is installed:

```bash
python manage.py check
```

---

## ⚙️ Configuration

### OpenWeatherMap API Key

Get a free API key from [OpenWeatherMap](https://openweathermap.org/api):

1. Sign up at https://openweathermap.org/
2. Navigate to API keys section
3. Generate a new API key
4. Add it to your environment:

**Windows:**
```powershell
$env:OPENWEATHER_API_KEY="your_api_key_here"
```

**Linux/Mac:**
```bash
export OPENWEATHER_API_KEY="your_api_key_here"
```

**Or add to `.env` file:**
```
OPENWEATHER_API_KEY=your_api_key_here
```

### Settings Configuration

The app is already added to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'weather_alerts',
]
```

---

## 🚀 Usage

### Manual Alert Generation

Generate alerts for all users:

```bash
python manage.py generate_weather_alerts
```

Force refresh weather data:

```bash
python manage.py generate_weather_alerts --force-refresh
```

### Scheduled Execution

#### Option 1: Cron (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add daily execution at 6 AM:
```
0 6 * * * cd /path/to/backend && /path/to/python manage.py generate_weather_alerts
```

#### Option 2: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 6:00 AM
4. Action: Start a program
5. Program: `C:\path\to\python.exe`
6. Arguments: `manage.py generate_weather_alerts`
7. Start in: `C:\path\to\backend`

#### Option 3: Celery Beat (Production)

Install Celery:
```bash
pip install celery redis
```

Create `backend/celery.py`:
```python
from celery import Celery
from celery.schedules import crontab

app = Celery('agri_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'generate-weather-alerts': {
        'task': 'weather_alerts.tasks.generate_alerts_task',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}
```

---

## 🔌 API Endpoints

Base URL: `/api/weather/`

### Get All Alerts
```http
GET /api/weather/alerts/
Authorization: Token {user_token}
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "unread_count": 2,
  "alerts": [
    {
      "id": 1,
      "disease_name": "Early Blight",
      "crop_name": "tomato",
      "alert_message": "High humidity and warm temperatures detected...",
      "is_read": false,
      "created_at": "2025-11-09T10:30:00Z",
      "weather_data": {
        "temperature": 28.5,
        "humidity": 75,
        "rainfall": 0
      }
    }
  ]
}
```

### Get Active/Unread Alerts
```http
GET /api/weather/alerts/active/
Authorization: Token {user_token}
```

### Mark Alert as Read
```http
POST /api/weather/alerts/{alert_id}/read/
Authorization: Token {user_token}
```

### Mark All Alerts as Read
```http
POST /api/weather/alerts/mark-all-read/
Authorization: Token {user_token}
```

### Refresh Alerts (Force Update)
```http
POST /api/weather/alerts/refresh/
Authorization: Token {user_token}
```

### Get Current Weather
```http
GET /api/weather/weather/
Authorization: Token {user_token}
```

---

## 💻 Management Commands

### generate_weather_alerts

Generates weather-based disease alerts for all users with configured crops.

**Usage:**
```bash
python manage.py generate_weather_alerts [options]
```

**Options:**
- `--force-refresh`: Force fetch new weather data even if cached data exists

**Example Output:**
```
============================================================
🌦️  WEATHER-BASED DISEASE ALERT GENERATION
============================================================
Force refresh enabled - will fetch new weather data

✅ Alert generation completed successfully!

📊 Statistics:
   Total users with crops: 25
   Users processed: 25
   Total alerts generated: 47
   Average alerts per user: 1.9
============================================================
```

---

## 📱 Frontend Integration

The Flutter app automatically displays weather alerts on the home page.

### Features:
- Alerts appear above "Our Services" section
- Beautiful red/orange gradient cards
- Shows disease name and affected crop
- Displays alert message with risk details
- "Get Treatment Advice" button links to diagnosis chat
- Dismiss button marks alert as read

### Sample Display:
```
┌─────────────────────────────────────┐
│ ⚠️ Weather Alerts              [2]  │
│ Disease risk warnings based on...   │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ 🦠 Early Blight              │    │
│ │ Tomato - High Risk          │    │
│ │                              │    │
│ │ ℹ️ Weather Alert             │    │
│ │ High humidity and warm...    │    │
│ │                              │    │
│ │ [Get Treatment Advice]       │    │
│ └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

---

## 📚 Knowledge Base

The system uses `weather_disease_kb.json` containing disease risk patterns:

### Structure:
```json
{
  "disease_name": "Early Blight",
  "crop_name": "tomato",
  "risk_conditions": {
    "min_humidity": 70,
    "max_temp": 32,
    "min_temp": 20,
    "alert": "High humidity and warm temperatures detected..."
  }
}
```

### Supported Conditions:
- `min_temp` / `max_temp`: Temperature range (°C)
- `min_humidity` / `max_humidity`: Humidity range (%)
- `min_rainfall` / `max_rainfall`: Rainfall amount (mm)

### Currently Tracked Diseases:

| Crop | Diseases |
|------|----------|
| Tomato | Early Blight, Late Blight |
| Potato | Late Blight |
| Rice | Rice Blast, Bacterial Leaf Blight |
| Wheat | Powdery Mildew, Rust |
| Apple | Downy Mildew, Fire Blight |
| Maize | Anthracnose, Southern Corn Leaf Blight |
| Chickpea | Bacterial Wilt, Ascochyta Blight |
| Kidney Beans | Fusarium Wilt, Angular Leaf Spot |
| And more... | (20+ diseases total) |

### Adding New Diseases:

Edit `weather_disease_kb.json` and add a new entry:

```json
{
  "disease_name": "New Disease",
  "crop_name": "new_crop",
  "risk_conditions": {
    "min_humidity": 80,
    "min_temp": 25,
    "max_temp": 35,
    "min_rainfall": 5,
    "alert": "Your custom alert message explaining the risk..."
  }
}
```

---

## 🔍 Admin Interface

Access the Django admin panel at `/admin/`:

### WeatherData Admin:
- View all cached weather data
- Filter by date
- Search by username

### WeatherAlert Admin:
- View all generated alerts
- Filter by read/unread status, date, disease
- Bulk action: "Mark selected alerts as read"
- Search by username, disease, or crop

---

## 🧪 Testing

### Test Alert Generation:

```bash
# Test for all users
python manage.py generate_weather_alerts

# Test with force refresh
python manage.py generate_weather_alerts --force-refresh
```

### Test API Endpoints:

Using curl:
```bash
# Get alerts
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/weather/alerts/

# Refresh alerts
curl -X POST -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/weather/alerts/refresh/
```

---

## 🐛 Troubleshooting

### No alerts generated?

1. **Check if users have crops configured:**
   - Users must have crops set in their profile
   - View in admin: `/admin/agri_app/userprofile/`

2. **Check weather API:**
   - Verify `OPENWEATHER_API_KEY` is set
   - Check logs for API errors

3. **Check knowledge base:**
   - Ensure crop names match between user profile and KB
   - Crop names are case-insensitive

### Weather data not updating?

- Use `--force-refresh` flag to bypass 1-hour cache
- Check API key is valid and has remaining calls

### Frontend not showing alerts?

1. Check API endpoint is accessible
2. Verify user is authenticated
3. Check browser console for errors
4. Ensure user has crops in profile

---

## 📈 Future Enhancements

- [ ] Add user location (lat/lon) to UserProfile model
- [ ] Implement push notifications for critical alerts
- [ ] Add multi-language support for alerts
- [ ] Create alert history and analytics
- [ ] Add weather forecast-based predictions (3-7 days)
- [ ] Implement SMS/email alerts
- [ ] Add crop-specific treatment recommendations
- [ ] Create weather dashboard with charts

---

## 📝 Notes

- Weather data is cached for 1 hour to reduce API calls
- Free OpenWeatherMap tier allows 1,000 calls/day
- Alerts are regenerated daily to avoid duplicates
- User must have crops configured in profile to receive alerts

---

## 🤝 Support

For issues or questions:
1. Check logs: `backend/logs/` (if logging is configured)
2. Run Django check: `python manage.py check`
3. Verify migrations: `python manage.py showmigrations weather_alerts`

---

**Built with ❤️ for CropGenius Agricultural Platform**

