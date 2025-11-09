"""
Script to train the crop recommendation model
Run this script to train/retrain the model with your dataset
"""

import os
import sys
import django
import logging

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')
django.setup()

from crop_recommendation.ml_pipeline import OptimizedCropRecommender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Train the crop recommendation model"""
    
    # Initialize recommender
    recommender = OptimizedCropRecommender(
        model_dir="./crop_models/",
        openweather_api_key="653c5d05ceab43cbae5e146f96e62499"
    )
    
    # Path to your dataset - UPDATE THIS PATH TO YOUR CSV FILE
    csv_path = "your_dataset.csv"  # Change this to your actual file name
    
    if not os.path.exists(csv_path):
        logger.error(f"Dataset not found at {csv_path}")
        logger.info("Please place your crop recommendation dataset at the specified path")
        return
    
    try:
        logger.info("Starting model training...")
        
        # Train models with hyperparameter optimization
        scores = recommender.train_models(csv_path, optimize=True)
        
        logger.info("Training completed successfully!")
        logger.info("Model scores:")
        for model_name, score in scores.items():
            logger.info(f"  {model_name}: {score:.4f}")
        
        logger.info(f"Best model: {recommender.best_model_name} with accuracy: {recommender.best_score:.4f}")
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise

if __name__ == "__main__":
    main()
