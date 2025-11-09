"""
Test script to verify crop recommendation API is working
"""

import os
import sys
import django
import requests
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')
django.setup()

from crop_recommendation.ml_pipeline import crop_recommender

def test_model_loading():
    """Test if the trained model loads correctly"""
    try:
        print("🔄 Loading trained model...")
        crop_recommender.load_models()
        print("✅ Model loaded successfully!")
        print(f"   Best model: {crop_recommender.best_model_name}")
        print(f"   Accuracy: {crop_recommender.best_score:.4f}")
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def test_prediction():
    """Test a sample prediction"""
    try:
        print("\n🔄 Testing prediction...")
        
        # Sample soil data
        result = crop_recommender.predict_crop(
            n=90.0,  # Nitrogen
            p=42.0,  # Phosphorus  
            k=43.0,  # Potassium
            ph=6.5   # pH level
        )
        
        print("✅ Prediction successful!")
        print(f"   Recommended crop: {result['predicted_crop']}")
        print(f"   Confidence: {result['confidence_score']:.4f}")
        print(f"   Alternative crops: {result['alternative_crops']}")
        return True
    except Exception as e:
        print(f"❌ Error in prediction: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Crop Recommendation System")
    print("=" * 50)
    
    # Test 1: Model loading
    if not test_model_loading():
        return
    
    # Test 2: Prediction
    if not test_prediction():
        return
    
    print("\n🎉 All tests passed! The system is ready for integration.")
    print("\n📱 Next steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Test API endpoints with your Flutter app")
    print("3. Use the crop recommendation feature in your app")

if __name__ == "__main__":
    main()
