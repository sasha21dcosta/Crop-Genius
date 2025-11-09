"""
Generate sample crop recommendation dataset for testing
This creates a realistic dataset with proper distributions
"""

import pandas as pd
import numpy as np
from typing import List, Dict

def generate_crop_dataset(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate a realistic crop recommendation dataset
    """
    
    # Define crop types and their typical soil/weather preferences
    crops = {
        'rice': {
            'n_range': (80, 120),
            'p_range': (30, 60),
            'k_range': (40, 80),
            'ph_range': (5.5, 7.0),
            'temp_range': (20, 35),
            'humidity_range': (70, 90),
            'rainfall_range': (100, 300)
        },
        'maize': {
            'n_range': (60, 100),
            'p_range': (20, 50),
            'k_range': (30, 70),
            'ph_range': (6.0, 7.5),
            'temp_range': (18, 30),
            'humidity_range': (50, 80),
            'rainfall_range': (50, 200)
        },
        'wheat': {
            'n_range': (40, 80),
            'p_range': (15, 40),
            'k_range': (20, 60),
            'ph_range': (6.0, 8.0),
            'temp_range': (10, 25),
            'humidity_range': (40, 70),
            'rainfall_range': (30, 150)
        },
        'cotton': {
            'n_range': (70, 110),
            'p_range': (25, 55),
            'k_range': (35, 75),
            'ph_range': (5.5, 8.0),
            'temp_range': (25, 40),
            'humidity_range': (40, 80),
            'rainfall_range': (20, 100)
        },
        'sugarcane': {
            'n_range': (100, 150),
            'p_range': (40, 80),
            'k_range': (50, 100),
            'ph_range': (6.0, 7.5),
            'temp_range': (20, 35),
            'humidity_range': (60, 90),
            'rainfall_range': (80, 250)
        },
        'potato': {
            'n_range': (50, 90),
            'p_range': (30, 70),
            'k_range': (40, 90),
            'ph_range': (4.5, 6.5),
            'temp_range': (15, 25),
            'humidity_range': (60, 85),
            'rainfall_range': (40, 120)
        },
        'tomato': {
            'n_range': (60, 100),
            'p_range': (25, 60),
            'k_range': (35, 80),
            'ph_range': (5.5, 7.0),
            'temp_range': (18, 30),
            'humidity_range': (50, 80),
            'rainfall_range': (30, 100)
        },
        'onion': {
            'n_range': (40, 80),
            'p_range': (20, 50),
            'k_range': (30, 70),
            'ph_range': (6.0, 7.5),
            'temp_range': (15, 28),
            'humidity_range': (40, 70),
            'rainfall_range': (20, 80)
        }
    }
    
    data = []
    
    for _ in range(n_samples):
        # Randomly select a crop
        crop_name = np.random.choice(list(crops.keys()))
        crop_params = crops[crop_name]
        
        # Generate data based on crop preferences with some noise
        n = np.random.normal(
            np.mean(crop_params['n_range']), 
            np.std(crop_params['n_range']) * 0.3
        )
        p = np.random.normal(
            np.mean(crop_params['p_range']), 
            np.std(crop_params['p_range']) * 0.3
        )
        k = np.random.normal(
            np.mean(crop_params['k_range']), 
            np.std(crop_params['k_range']) * 0.3
        )
        ph = np.random.normal(
            np.mean(crop_params['ph_range']), 
            np.std(crop_params['ph_range']) * 0.2
        )
        temperature = np.random.normal(
            np.mean(crop_params['temp_range']), 
            np.std(crop_params['temp_range']) * 0.3
        )
        humidity = np.random.normal(
            np.mean(crop_params['humidity_range']), 
            np.std(crop_params['humidity_range']) * 0.2
        )
        rainfall = np.random.normal(
            np.mean(crop_params['rainfall_range']), 
            np.std(crop_params['rainfall_range']) * 0.4
        )
        
        # Ensure values are within reasonable bounds
        n = max(0, min(200, n))
        p = max(0, min(200, p))
        k = max(0, min(200, k))
        ph = max(0, min(14, ph))
        temperature = max(-10, min(50, temperature))
        humidity = max(0, min(100, humidity))
        rainfall = max(0, min(500, rainfall))
        
        data.append({
            'N': round(n, 1),
            'P': round(p, 1),
            'K': round(k, 1),
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'ph': round(ph, 1),
            'rainfall': round(rainfall, 1),
            'label': crop_name
        })
    
    return pd.DataFrame(data)

def main():
    """Generate and save sample dataset"""
    print("Generating sample crop recommendation dataset...")
    
    # Generate dataset
    df = generate_crop_dataset(n_samples=2000)
    
    # Save to CSV
    df.to_csv('Crop_recommendation.csv', index=False)
    
    print(f"Dataset generated with {len(df)} samples")
    print(f"Columns: {list(df.columns)}")
    print(f"Crop distribution:")
    print(df['label'].value_counts())
    
    # Show sample data
    print("\nSample data:")
    print(df.head())

if __name__ == "__main__":
    main()
