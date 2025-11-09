# 🌾 Real-Time Crop Prices Module - Setup Guide

## ✅ What Has Been Implemented

A complete real-time crop prices module has been added to your CropGenius application, featuring:

### Backend (Django)
1. **New Django App:** `crop_prices` with complete REST API
2. **Helper Functions:** Fetch price data from AGMARKNET API
3. **Smart Caching:** Reduces API calls and improves performance
4. **Automatic Fallback:** Shows most recent data if today's prices aren't available
5. **Multiple Endpoints:** Single query, bulk query, crops list, states list

### Frontend (Flutter)
1. **Beautiful UI:** Modern, user-friendly crop prices screen
2. **Quick Selection:** Popular crops for easy access
3. **Smart Filters:** State and district selection
4. **Rich Display:** Shows price per kg and per quintal
5. **Error Handling:** Clear messages for missing data
6. **Info Section:** Explains data source and updates

## 📁 Files Created/Modified

### New Files Created:
```
backend/crop_prices/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── tests.py
├── utils.py          # Helper functions for AGMARKNET API
├── views.py          # REST API endpoints
├── urls.py           # URL routing
└── README.md         # Module documentation

backend/test_crop_prices_api.py    # Test script

frontend/lib/crop_prices.dart      # Flutter UI screen
```

### Modified Files:
```
backend/agri_backend/settings.py   # Added 'crop_prices' to INSTALLED_APPS
backend/agri_backend/urls.py       # Added crop_prices URLs
frontend/lib/home.dart             # Added navigation and import
```

## 🚀 How to Use

### 1. Start the Django Server

```bash
cd backend
python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/crop-prices/`

### 2. Test the API (Optional)

Run the test script to verify everything works:

```bash
cd backend
python test_crop_prices_api.py
```

### 3. Run the Flutter App

```bash
cd frontend
flutter run
```

### 4. Access from Home Screen

1. Open the app
2. Look for "Real-Time Crop Prices" card on the home screen
3. Tap it to open the crop prices screen
4. Select a crop (or choose from popular crops)
5. Select state and district
6. Tap "Get Price" to fetch current market prices

## 📡 API Endpoints

### Get Single Crop Price
```http
GET /api/crop-prices/?crop_name=Tomato&state=Maharashtra&district=Nashik
```

### Get Available Crops
```http
GET /api/crop-prices/crops/
```

### Get Available States
```http
GET /api/crop-prices/states/
```

### Bulk Query (POST)
```http
POST /api/crop-prices/bulk/
Content-Type: application/json

{
  "queries": [
    {"crop_name": "Tomato", "state": "Maharashtra", "district": "Nashik"},
    {"crop_name": "Onion", "state": "Maharashtra", "district": "Pune"}
  ]
}
```

## 🔑 API Configuration

The AGMARKNET API configuration is in `crop_prices/utils.py`:

```python
AGMARKNET_API_BASE = "https://api.data.gov.in/resource"
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
```

### Getting Your Own API Key (Recommended)

1. Visit https://data.gov.in
2. Create a free account
3. Generate an API key
4. Replace the API_KEY in `utils.py` with your key

The current key is a public demo key and may have rate limits.

## ⚙️ How It Works

1. **User Query:** User enters crop name, state, and district
2. **Cache Check:** System checks if data is cached (1-hour cache)
3. **API Call:** If not cached, fetches from AGMARKNET API
4. **Date Fallback:** If today's data unavailable, searches up to 7 days back
5. **Response:** Returns price data with market information
6. **Display:** Flutter app shows formatted price information

## 🎨 Features Implemented

### Smart Features:
✅ Real-time price fetching from government API  
✅ Automatic caching (1 hour for prices, 24 hours for crops list)  
✅ Fallback to most recent data if today's prices unavailable  
✅ No database required (direct API integration)  
✅ Bulk query support for multiple crops  
✅ Error handling and user-friendly messages  

### UI Features:
✅ Popular crops quick selection  
✅ State dropdown with all Indian states  
✅ Beautiful gradient design  
✅ Price per kg and per quintal display  
✅ Market and date information  
✅ Cached data indicator  
✅ Info section about data source  

## 🔍 Testing Examples

### Test with cURL:

```bash
# Single crop price
curl "http://localhost:8000/api/crop-prices/?crop_name=Tomato&state=Maharashtra&district=Nashik"

# Available crops
curl "http://localhost:8000/api/crop-prices/crops/"

# Available states
curl "http://localhost:8000/api/crop-prices/states/"
```

### Test with Python:

```python
import requests

# Get tomato price
response = requests.get(
    'http://localhost:8000/api/crop-prices/',
    params={
        'crop_name': 'Tomato',
        'state': 'Maharashtra',
        'district': 'Nashik'
    }
)

print(response.json())
```

## 📱 Mobile App Usage

1. **Quick Selection:**
   - Tap any popular crop chip for instant selection
   - Or type custom crop name in the text field

2. **Location:**
   - Select state from dropdown
   - Enter district name (e.g., "Nashik", "Pune")

3. **Get Price:**
   - Tap the "Get Price" button
   - Wait for results (usually instant if cached)

4. **View Results:**
   - See price per kg (main display)
   - View modal price per quintal
   - Check market name and date
   - "CACHED" badge shows if data is from cache

## ⚠️ Important Notes

### Data Availability:
- AGMARKNET data may not be available for all crops in all locations
- Some markets update daily, others less frequently
- The system automatically finds the most recent data available

### API Rate Limits:
- The public demo API key has rate limits
- Consider getting your own API key for production use
- Caching helps reduce API calls

### Network Requirements:
- Backend needs internet to fetch from AGMARKNET
- Flutter app needs network connection to backend
- Consider implementing offline mode with cached historical data

## 🐛 Troubleshooting

### Issue: "No price data available"
**Solution:** 
- Try a different district in the same state
- Try a more common crop (Tomato, Onion, Rice)
- Check if AGMARKNET has data for that location

### Issue: API timeout
**Solution:**
- Check internet connection
- Verify AGMARKNET API is accessible
- Increase timeout in `utils.py` (currently 10 seconds)

### Issue: Django server error
**Solution:**
- Check if 'crop_prices' is in INSTALLED_APPS
- Verify URLs are properly configured
- Check Django logs for detailed error

### Issue: Flutter navigation not working
**Solution:**
- Verify `crop_prices.dart` is imported in `home.dart`
- Check for any Flutter build errors
- Run `flutter clean` and rebuild

## 🔄 Future Enhancements

Possible improvements you can add:

1. **Historical Data:** Show price trends over time with charts
2. **Price Alerts:** Notify farmers when prices reach target levels
3. **Comparison:** Compare prices across multiple markets
4. **Favorites:** Save frequently checked crops
5. **Offline Mode:** Cache data for offline viewing
6. **Multi-language:** Support regional languages for crop names
7. **Export:** Allow farmers to export price data
8. **Predictions:** Add ML-based price prediction

## 📞 Support

### AGMARKNET Information:
- Website: https://agmarknet.gov.in
- API Portal: https://data.gov.in

### Django Documentation:
- https://docs.djangoproject.com

### Flutter Documentation:
- https://flutter.dev/docs

## ✅ Summary

Your CropGenius app now has a fully functional real-time crop prices module! Farmers can:
- Check current market prices from government data
- Compare prices across different regions
- Access data quickly with smart caching
- Use a beautiful, intuitive mobile interface

The implementation follows best practices:
- Clean, modular code
- Comprehensive error handling
- User-friendly UI/UX
- Efficient caching strategy
- RESTful API design
- Detailed documentation

**Ready to use! 🎉**

