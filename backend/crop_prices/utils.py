"""
Helper functions to fetch real-time crop prices from AGMARKNET API
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# AGMARKNET API Configuration
# Note: Replace with actual API key when available
AGMARKNET_API_BASE = "https://api.data.gov.in/resource"
AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"  # Current Daily Price resource ID
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"  # Public demo key - replace with actual key


def fetch_crop_price(crop_name: str, state: str, district: str) -> Dict:
    """
    Fetch and return the most recent crop price from AGMARKNET API.
    
    Args:
        crop_name: Name of the crop/commodity (e.g., 'Tomato', 'Onion')
        state: State name (e.g., 'Maharashtra')
        district: District name (e.g., 'Nashik')
    
    Returns:
        Dictionary containing crop price data or error message
    """
    try:
        # Try to fetch data for today first
        today = datetime.now()
        
        # Search for data starting from today, going back up to 7 days
        for days_back in range(8):
            target_date = today - timedelta(days=days_back)
            date_str = target_date.strftime("%d/%m/%Y")
            
            logger.info(f"Searching for {crop_name} price in {district}, {state} for date: {date_str}")
            
            # Build API request URL
            # Note: Adjust filters based on actual AGMARKNET API field names
            params = {
                "api-key": API_KEY,
                "format": "json",
                "limit": 100,  # Fetch multiple records to find best match
                "filters[commodity]": crop_name,
                "filters[state]": state,
                "filters[district]": district,
                "filters[arrival_date]": date_str,
            }
            
            url = f"{AGMARKNET_API_BASE}/{AGMARKNET_RESOURCE_ID}"
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we got any records
            if data.get("records") and len(data["records"]) > 0:
                record = data["records"][0]
                
                # Extract price information
                # Note: Field names may vary - adjust based on actual API response
                modal_price = float(record.get("modal_price", 0))
                market_name = record.get("market", "Unknown Market")
                
                # Convert to per kg price (assuming modal price is per quintal)
                price_per_kg = round(modal_price / 100, 2) if modal_price > 0 else 0
                
                return {
                    "crop_name": crop_name,
                    "market": market_name,
                    "state": state,
                    "district": district,
                    "modal_price_per_quintal": modal_price,
                    "price_per_kg": price_per_kg,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "unit": "₹/kg",
                    "success": True
                }
        
        # If no data found in the last 7 days
        logger.warning(f"No price data found for {crop_name} in {district}, {state}")
        return {
            "error": f"No price data available for {crop_name} in {district} or nearby dates",
            "success": False
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return {
            "error": f"Failed to fetch price data: {str(e)}",
            "success": False
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "error": f"An error occurred: {str(e)}",
            "success": False
        }


def get_available_crops() -> list:
    """
    Get list of available crops/commodities from AGMARKNET.
    
    Returns:
        List of crop names
    """
    try:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 1000,
        }
        
        url = f"{AGMARKNET_API_BASE}/{AGMARKNET_RESOURCE_ID}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("records"):
            # Extract unique commodity names
            crops = set()
            for record in data["records"]:
                commodity = record.get("commodity")
                if commodity:
                    crops.add(commodity)
            
            return sorted(list(crops))
        
        return []
    
    except Exception as e:
        logger.error(f"Failed to fetch available crops: {str(e)}")
        return []


def get_available_states() -> list:
    """
    Get list of available states from AGMARKNET.
    
    Returns:
        List of state names
    """
    # Common Indian states where AGMARKNET operates
    return [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
    ]

