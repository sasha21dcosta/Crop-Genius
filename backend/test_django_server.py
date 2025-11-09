"""
Test Django server and crop recommendation API
"""

import requests
import json

def test_django_server():
    """Test if Django server is running and API works"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Django Server")
    print("=" * 40)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/api/crop/model-info/", timeout=5)
        if response.status_code == 200:
            print("✅ Django server is running")
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Django server is not running")
        print("   Start it with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False
    
    # Test 2: Test model info endpoint
    try:
        response = requests.get(f"{base_url}/api/crop/model-info/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Model info endpoint working")
            print(f"   Model: {data.get('model_info', {}).get('model_name', 'Unknown')}")
        else:
            print(f"⚠️ Model info endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing model info: {e}")
    
    # Test 3: Test crop recommendation (without auth for now)
    try:
        test_data = {
            "n_content": 90.0,
            "p_content": 42.0,
            "k_content": 43.0,
            "ph": 6.5
        }
        
        response = requests.post(
            f"{base_url}/api/crop/recommend/",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Crop recommendation API working!")
            print(f"   Recommended crop: {data.get('recommendation', {}).get('predicted_crop', 'Unknown')}")
            print(f"   Confidence: {data.get('recommendation', {}).get('confidence_score', 0):.4f}")
        else:
            print(f"⚠️ Crop recommendation API error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing crop recommendation: {e}")
    
    print("\n🎯 Next steps:")
    print("1. If all tests pass, your Flutter app should work!")
    print("2. Update baseUrl in Flutter auth_service.dart to: http://localhost:8000")
    print("3. Test the Flutter app crop recommendation feature")

if __name__ == "__main__":
    test_django_server()


