# 🚀 Quick Setup Guide - Weather Alerts

Follow these steps to get the weather-based disease alert system running:

---

## Step 1: Run Database Migrations

```bash
cd backend
python manage.py migrate
```

This creates the `WeatherData` and `WeatherAlert` tables.

---

## Step 2: Get OpenWeatherMap API Key (Optional but Recommended)

1. Visit https://openweathermap.org/api
2. Sign up for a free account
3. Generate an API key
4. Set the environment variable:

**Windows PowerShell:**
```powershell
$env:OPENWEATHER_API_KEY="your_api_key_here"
```

**Command Prompt:**
```cmd
set OPENWEATHER_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export OPENWEATHER_API_KEY=your_api_key_here
```

> **Note:** Without an API key, the system will use default weather values for testing.

---

## Step 3: Verify Installation

```bash
python manage.py check weather_alerts
```

You should see: `System check identified no issues (0 silenced).`

---

## Step 4: Test Alert Generation

Make sure you have at least one user with crops configured in their profile, then run:

```bash
python manage.py generate_weather_alerts
```

**Expected output:**
```
============================================================
🌦️  WEATHER-BASED DISEASE ALERT GENERATION
============================================================
✅ Alert generation completed successfully!

📊 Statistics:
   Total users with crops: X
   Users processed: X
   Total alerts generated: X
============================================================
```

---

## Step 5: Start Django Server

```bash
python manage.py runserver
```

---

## Step 6: Test API Endpoints

### Test in Browser (requires authentication):
```
http://localhost:8000/api/weather/alerts/active/
```

### Test with curl:
```bash
# Replace YOUR_TOKEN with actual user token
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/weather/alerts/active/
```

---

## Step 7: Run Flutter App

The Flutter app should automatically display alerts on the home page!

---

## 📝 Important Notes

### For alerts to appear:

1. ✅ Users must have crops configured in their profile
2. ✅ Weather conditions must match disease risk patterns
3. ✅ Run `generate_weather_alerts` command at least once
4. ✅ Flutter app must be able to reach your Django backend

### To configure user crops:

**Option 1: Via Admin Panel**
1. Go to http://localhost:8000/admin/
2. Navigate to `User Profiles`
3. Edit a user profile
4. Select crops (e.g., "rice,tomato,wheat")
5. Save

**Option 2: Via Flutter App**
- Users can select crops in their profile settings

---

## 🔄 Daily Scheduled Execution

### Windows Task Scheduler:

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task → Name it "Weather Alerts"
3. Trigger: Daily at 6:00 AM
4. Action: Start a program
   - Program: `C:\path\to\python.exe`
   - Arguments: `manage.py generate_weather_alerts`
   - Start in: `C:\Users\Sasha\StudioProjects\CropGenius\backend`

### Linux/Mac Cron:

```bash
crontab -e
```

Add this line:
```
0 6 * * * cd /path/to/backend && /path/to/venv/bin/python manage.py generate_weather_alerts
```

---

## 🧪 Testing Scenarios

### Scenario 1: Create Test Alert for Tomato
1. Set user's crops to include "tomato"
2. The system will check for tomato-related diseases
3. If weather matches (e.g., high humidity), alert is generated

### Scenario 2: Force Refresh Weather
```bash
python manage.py generate_weather_alerts --force-refresh
```

### Scenario 3: View Alerts in Admin
1. Go to http://localhost:8000/admin/weather_alerts/weatheralert/
2. See all generated alerts
3. Filter by user, disease, or read status

---

## 🎯 Quick Test Checklist

- [ ] Migrations completed successfully
- [ ] OpenWeatherMap API key configured (optional)
- [ ] At least one user has crops in profile
- [ ] `generate_weather_alerts` command runs without errors
- [ ] Alerts visible in Django admin
- [ ] API endpoint `/api/weather/alerts/active/` returns data
- [ ] Flutter app shows alerts on home page
- [ ] Can dismiss alerts by tapping X button

---

## 📊 Monitoring

### Check number of alerts:
```bash
python manage.py shell
```

```python
from weather_alerts.models import WeatherAlert
print(f"Total alerts: {WeatherAlert.objects.count()}")
print(f"Unread alerts: {WeatherAlert.objects.filter(is_read=False).count()}")
```

### View latest weather data:
```python
from weather_alerts.models import WeatherData
weather = WeatherData.objects.first()
if weather:
    print(f"Temperature: {weather.temperature}°C")
    print(f"Humidity: {weather.humidity}%")
    print(f"Rainfall: {weather.rainfall}mm")
```

---

## ❓ Troubleshooting

### Problem: No alerts generated

**Solution:**
1. Check if users have crops: `python manage.py shell` → Check UserProfile crops
2. Verify weather conditions match disease patterns
3. Check logs for errors

### Problem: API returns empty array

**Solution:**
1. Run `python manage.py generate_weather_alerts` first
2. Check user authentication token
3. Verify user has crops configured

### Problem: Flutter not showing alerts

**Solution:**
1. Check console for errors
2. Verify `baseUrl` in `auth_service.dart` is correct
3. Ensure user token is valid
4. Test API directly with curl/Postman

---

## 🎉 Success!

If you've completed all steps, you should now have:
- ✅ Weather alerts system fully functional
- ✅ Automatic risk detection based on weather
- ✅ Beautiful alerts displayed in Flutter app
- ✅ Ability to schedule daily alert generation

**For detailed documentation, see `WEATHER_ALERTS_GUIDE.md`**

---

**Need help? Check the main guide or Django logs for more details!**

