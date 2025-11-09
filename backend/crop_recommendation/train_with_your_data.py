"""
Train the crop recommendation model with your existing CSV file
Usage: python train_with_your_data.py path/to/your/dataset.csv
"""

import os
import sys
import django
import logging
import argparse

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')
django.setup()

from crop_recommendation.ml_pipeline import OptimizedCropRecommender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Train the crop recommendation model with your dataset"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train crop recommendation model')
    parser.add_argument('csv_path', help='Path to your CSV dataset')
    parser.add_argument('--optimize', action='store_true', default=True, 
                       help='Enable hyperparameter optimization (default: True)')
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.csv_path):
        logger.error(f"Dataset not found at {args.csv_path}")
        logger.info("Please provide the correct path to your CSV file")
        return
    
    # Initialize recommender
    recommender = OptimizedCropRecommender(
        model_dir="./crop_models/",
        openweather_api_key="653c5d05ceab43cbae5e146f96e62499"
    )
    
    try:
        logger.info(f"Starting model training with dataset: {args.csv_path}")
        logger.info(f"Hyperparameter optimization: {'Enabled' if args.optimize else 'Disabled'}")
        
        # Train models with hyperparameter optimization
        scores = recommender.train_models(args.csv_path, optimize=args.optimize)
        
        logger.info("Training completed successfully!")
        logger.info("Model performance scores:")
        for model_name, score in scores.items():
            logger.info(f"  {model_name}: {score:.4f} ({score*100:.2f}%)")
        
        logger.info(f"Best model: {recommender.best_model_name} with accuracy: {recommender.best_score:.4f} ({recommender.best_score*100:.2f}%)")
        
        # Show dataset info
        import pandas as pd
        df = pd.read_csv(args.csv_path)
        logger.info(f"Dataset info:")
        logger.info(f"  Total samples: {len(df)}")
        logger.info(f"  Features: {list(df.columns)}")
        logger.info(f"  Crop types: {df['label'].nunique()}")
        logger.info(f"  Crop distribution:")
        for crop, count in df['label'].value_counts().items():
            logger.info(f"    {crop}: {count} samples")
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise

if __name__ == "__main__":
    main()
