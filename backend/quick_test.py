"""
Quick test of the crop recommendation system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crop_recommendation.ml_pipeline import OptimizedCropRecommender

def test_system():
    """Test the crop recommendation system"""
    print("🧪 Quick Test - Crop Recommendation System")
    print("=" * 50)
    
    try:
        # Initialize recommender
        print("🔄 Initializing system...")
        recommender = OptimizedCropRecommender(
            model_dir="./crop_models/",
            openweather_api_key="653c5d05ceab43cbae5e146f96e62499"
        )
        
        # Load models
        print("🔄 Loading trained models...")
        recommender.load_models()
        print(f"✅ Model loaded: {recommender.best_model_name}")
        print(f"✅ Accuracy: {recommender.best_score:.4f}")
        
        # Test prediction
        print("\n🔄 Testing prediction...")
        result = recommender.predict_crop(
            n=90.0,  # Nitrogen
            p=42.0,  # Phosphorus  
            k=43.0,  # Potassium
            ph=6.5   # pH level
        )
        
        print("✅ Prediction successful!")
        print(f"   Recommended crop: {result['predicted_crop']}")
        print(f"   Confidence: {result['confidence_score']:.4f}")
        print(f"   Alternative crops: {result['alternative_crops'][:3]}")
        
        print("\n🎉 System is working perfectly!")
        print("✅ Ready for Flutter app integration!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure models are trained: python crop_recommendation/train_with_your_data.py Crop_recommendation.csv")
        print("2. Check if crop_models/ directory exists")
        print("3. Verify model files are present")

if __name__ == "__main__":
    test_system()
