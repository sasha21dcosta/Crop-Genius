# Real-Time Crop Prices Module

This Django module provides real-time crop price data to farmers using AGMARKNET (Government of India's agricultural marketing data).

## Features

✅ Fetch real-time crop prices from AGMARKNET API  
✅ Automatic fallback to most recent data if today's data is unavailable  
✅ Built-in caching to reduce API calls and improve performance  
✅ RESTful API endpoints for easy integration  
✅ Support for bulk price queries  
✅ No database storage required (direct API integration)

## API Endpoints

### 1. Get Crop Price
```
GET /api/crop-prices/?crop_name=Tomato&state=Maharashtra&district=Nashik
```

**Query Parameters:**
- `crop_name` (required): Name of the crop/commodity (e.g., Tomato, Onion, Rice)
- `state` (required): State name (e.g., Maharashtra, Punjab)
- `district` (required): District name (e.g., Nashik, Pune)

**Response (Success):**
```json
{
  "crop_name": "Tomato",
  "market": "Nashik APMC",
  "state": "Maharashtra",
  "district": "Nashik",
  "modal_price_per_quintal": 2450,
  "price_per_kg": 24.50,
  "date": "2025-11-09",
  "unit": "₹/kg",
  "success": true,
  "cached": false
}
```

**Response (Error):**
```json
{
  "error": "No price data available for Tomato in Nashik or nearby dates",
  "success": false
}
```

### 2. Get Available Crops
```
GET /api/crop-prices/crops/
```

Returns a list of available crops/commodities.

### 3. Get Available States
```
GET /api/crop-prices/states/
```

Returns a list of states where AGMARKNET operates.

### 4. Bulk Price Query
```
POST /api/crop-prices/bulk/
Content-Type: application/json

{
  "queries": [
    {"crop_name": "Tomato", "state": "Maharashtra", "district": "Nashik"},
    {"crop_name": "Onion", "state": "Maharashtra", "district": "Pune"}
  ]
}
```

Fetch prices for multiple crops in a single request (maximum 10 queries).

## Configuration

The AGMARKNET API configuration is in `utils.py`:

```python
AGMARKNET_API_BASE = "https://api.data.gov.in/resource"
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
```

**Note:** Replace the API_KEY with your own key from data.gov.in if needed.

## Caching

The module uses Django's built-in caching:
- Crop prices: cached for 1 hour (3600 seconds)
- Available crops: cached for 24 hours (86400 seconds)

This reduces API calls and improves response times.

## Data Source

Data is fetched from:
- **AGMARKNET** - Agricultural Marketing Information Network
- **API Provider:** data.gov.in (Government of India)
- **Dataset:** Current Daily Price of Various Commodities in Various Markets (Mandi)

## Date Handling

If today's price data is not available, the API automatically searches backwards up to 7 days to find the most recent available price. This ensures farmers always get the latest market information even if real-time data is delayed.

## Error Handling

The module includes comprehensive error handling:
- API request failures
- Network errors
- Missing or invalid data
- Timeout handling (10-second timeout)

## Installation

1. The module is already integrated into your Django project
2. Make sure `requests` is in your requirements.txt (already included)
3. The app is registered in `INSTALLED_APPS`
4. URLs are configured in main `urls.py`

## Testing

Test the API using curl:

```bash
# Test single crop price
curl "http://localhost:8000/api/crop-prices/?crop_name=Tomato&state=Maharashtra&district=Nashik"

# Test available crops
curl "http://localhost:8000/api/crop-prices/crops/"

# Test available states
curl "http://localhost:8000/api/crop-prices/states/"
```

## Flutter Integration

The Flutter app includes a beautiful UI (`crop_prices.dart`) that:
- Provides quick selection of popular crops
- Allows filtering by state and district
- Displays prices in an easy-to-read format
- Shows both per kg and per quintal prices
- Indicates data freshness and source

## Future Enhancements

Possible improvements:
- Historical price trends and charts
- Price comparison across multiple markets
- Price alerts when crop prices change significantly
- Offline support with cached historical data
- Multi-language support for crop names
- Integration with farmer's saved crops for automatic price updates

## Support

For issues or questions about the AGMARKNET API:
- Visit: https://data.gov.in
- AGMARKNET Portal: https://agmarknet.gov.in

## License

This module is part of the CropGenius agricultural application.

