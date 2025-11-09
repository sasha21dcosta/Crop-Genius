"""
Test script for the Crop Prices API
Run this script to test the real-time crop prices module

Usage:
    python test_crop_prices_api.py
    python test_crop_prices_api.py https://your-server.com

Note: Update BASE_URL below to match your server URL
"""
import requests
import json
import sys

# Change this to your actual server URL (dev tunnel, ngrok, production, etc.)
BASE_URL = "http://localhost:8000/api/crop-prices"

# Allow command-line override
if len(sys.argv) > 1:
    BASE_URL = f"{sys.argv[1]}/api/crop-prices"
    print(f"Using custom URL: {BASE_URL}")

def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")

def test_single_crop_price():
    """Test fetching price for a single crop"""
    print_section("TEST 1: Single Crop Price Query")
    
    params = {
        "crop_name": "Tomato",
        "state": "Maharashtra",
        "district": "Nashik"
    }
    
    print(f"📡 Requesting: {BASE_URL}")
    print(f"📋 Parameters: {json.dumps(params, indent=2)}\n")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        print(f"✅ Status Code: {response.status_code}")
        
        data = response.json()
        print(f"📊 Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if response.status_code == 200 and data.get('success'):
            print(f"\n✅ SUCCESS: Found price for {data['crop_name']}")
            print(f"   💰 Price: ₹{data['price_per_kg']}/kg")
            print(f"   📍 Market: {data['market']}")
            print(f"   📅 Date: {data['date']}")
        else:
            print(f"\n⚠️  No data found or error occurred")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {str(e)}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")

def test_available_crops():
    """Test fetching available crops list"""
    print_section("TEST 2: Available Crops")
    
    url = f"{BASE_URL}/crops/"
    print(f"📡 Requesting: {url}\n")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"✅ Status Code: {response.status_code}")
        
        data = response.json()
        
        if 'crops' in data:
            crops = data['crops']
            print(f"📊 Found {len(crops)} crops")
            if crops:
                print(f"🌾 First 10 crops: {', '.join(crops[:10])}")
            print(f"💾 Cached: {data.get('cached', False)}")
        else:
            print(f"📊 Response:")
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {str(e)}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")

def test_available_states():
    """Test fetching available states list"""
    print_section("TEST 3: Available States")
    
    url = f"{BASE_URL}/states/"
    print(f"📡 Requesting: {url}\n")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        
        data = response.json()
        
        if 'states' in data:
            states = data['states']
            print(f"📊 Found {len(states)} states")
            print(f"🗺️  States: {', '.join(states[:5])}... (showing first 5)")
        else:
            print(f"📊 Response:")
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {str(e)}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")

def test_bulk_query():
    """Test bulk price query"""
    print_section("TEST 4: Bulk Price Query")
    
    url = f"{BASE_URL}/bulk/"
    payload = {
        "queries": [
            {"crop_name": "Tomato", "state": "Maharashtra", "district": "Nashik"},
            {"crop_name": "Onion", "state": "Maharashtra", "district": "Pune"},
            {"crop_name": "Rice", "state": "Punjab", "district": "Ludhiana"}
        ]
    }
    
    print(f"📡 Requesting: {url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(f"✅ Status Code: {response.status_code}")
        
        data = response.json()
        
        if 'results' in data:
            results = data['results']
            print(f"📊 Received {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                if result.get('success'):
                    print(f"  ✅ {result['crop_name']}: ₹{result['price_per_kg']}/kg ({result['date']})")
                else:
                    print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"📊 Response:")
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {str(e)}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")

def test_error_handling():
    """Test API error handling"""
    print_section("TEST 5: Error Handling")
    
    # Test missing parameters
    print("Testing missing parameters...\n")
    
    try:
        response = requests.get(BASE_URL, params={"crop_name": "Tomato"}, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        data = response.json()
        print(f"📊 Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 400:
            print("\n✅ Correctly returns 400 for missing parameters")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    print("\n" + "=" * 60)
    print("  🌾 CROP PRICES API TEST SUITE 🌾")
    print("=" * 60)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure your Django server is running and accessible")
    print("Press Ctrl+C to cancel\n")
    
    try:
        input("Press Enter to start tests...")
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
        sys.exit(0)
    
    # Run all tests
    test_single_crop_price()
    test_available_crops()
    test_available_states()
    test_bulk_query()
    test_error_handling()
    
    print_section("🎉 ALL TESTS COMPLETED")
    print("Review the results above to verify the API is working correctly.\n")

if __name__ == "__main__":
    main()

