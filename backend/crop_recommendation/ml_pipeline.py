"""
Optimized Crop Recommendation ML Pipeline
Features:
- Multiple ML algorithms (XGBoost, LightGBM, CatBoost, RandomForest)
- Hyperparameter optimization with Optuna
- Cross-validation and proper evaluation
- Feature engineering and selection
- Model versioning and performance tracking
- Robust error handling and logging
"""

import os
import logging
import pickle
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import requests
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
import joblib

# Enhanced ML libraries
import xgboost as xgb
import lightgbm as lgb
# from catboost import CatBoostClassifier  # Requires Rust - commented out
import optuna
from optuna.samplers import TPESampler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedCropRecommender:
    """
    Advanced crop recommendation system with multiple algorithms and optimization
    """
    
    def __init__(self, model_dir: str = "./crop_models/", openweather_api_key: str = None):
        self.model_dir = model_dir
        self.openweather_api_key = openweather_api_key or os.getenv("OPENWEATHER_API_KEY")
        self.models = {}
        self.scaler = None
        self.label_encoder = None
        self.feature_names = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        self.best_model = None
        self.best_score = 0
        
        # Create model directory
        os.makedirs(model_dir, exist_ok=True)
        
    def get_location_by_ip(self) -> Tuple[float, float]:
        """Get approximate latitude and longitude based on public IP"""
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            loc = data.get("loc")
            if loc:
                lat, lon = map(float, loc.split(","))
                return lat, lon
        except Exception as e:
            logger.warning(f"Error detecting location: {e}")
        
        # Fallback to India coordinates
        return 20.5937, 78.9629
    
    def fetch_weather_data(self, lat: float, lon: float) -> Dict[str, float]:
        """Fetch current weather data from OpenWeather API"""
        if not self.openweather_api_key:
            logger.warning("No OpenWeather API key provided, using default values")
            return {"temperature": 25.0, "humidity": 70.0, "rainfall": 0.0}
        
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.openweather_api_key}&units=metric"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            rainfall = data.get('rain', {}).get('1h', 0.0)
            
            return {
                "temperature": temp,
                "humidity": humidity,
                "rainfall": rainfall
            }
        except Exception as e:
            logger.warning(f"Error fetching weather data: {e}")
            return {"temperature": 25.0, "humidity": 70.0, "rainfall": 0.0}
    
    def load_and_preprocess_data(self, csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Load and preprocess the crop recommendation dataset"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded dataset with shape: {df.shape}")
            
            # Validate required columns
            required_cols = self.feature_names + ['label']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing columns: {missing_cols}")
            
            # Handle missing values
            df = df.dropna()
            
            # Feature engineering
            df = self._engineer_features(df)
            
            # Prepare features and target
            X = df[self.feature_names].values
            y = df['label'].values
            
            logger.info(f"Preprocessed data shape: X={X.shape}, y={y.shape}")
            return X, y
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer additional features for better predictions"""
        # Add soil nutrient ratios
        df['N_P_ratio'] = df['N'] / (df['P'] + 1e-8)
        df['N_K_ratio'] = df['N'] / (df['K'] + 1e-8)
        df['P_K_ratio'] = df['P'] / (df['K'] + 1e-8)
        
        # Add weather combinations
        df['temp_humidity'] = df['temperature'] * df['humidity']
        df['temp_rainfall'] = df['temperature'] * df['rainfall']
        
        # Add soil quality indicators
        df['soil_quality'] = (df['N'] + df['P'] + df['K']) / 3
        
        # Update feature names
        self.feature_names.extend(['N_P_ratio', 'N_K_ratio', 'P_K_ratio', 
                                 'temp_humidity', 'temp_rainfall', 'soil_quality'])
        
        return df
    
    def optimize_hyperparameters(self, X: np.ndarray, y: np.ndarray, 
                              algorithm: str = 'xgboost', n_trials: int = 50) -> Dict:
        """Optimize hyperparameters using Optuna"""
        
        def objective(trial):
            if algorithm == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'random_state': 42
                }
                model = xgb.XGBClassifier(**params)
                
            elif algorithm == 'lightgbm':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'random_state': 42,
                    'verbose': -1
                }
                model = lgb.LGBMClassifier(**params)
                
            # CatBoost removed - requires Rust installation
            
            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
            return cv_scores.mean()
        
        study = optuna.create_study(direction='maximize', sampler=TPESampler())
        study.optimize(objective, n_trials=n_trials)
        
        logger.info(f"Best {algorithm} parameters: {study.best_params}")
        logger.info(f"Best {algorithm} score: {study.best_value:.4f}")
        
        return study.best_params
    
    def train_models(self, csv_path: str, optimize: bool = True) -> Dict[str, float]:
        """Train multiple models and select the best one"""
        try:
            # Load and preprocess data
            X, y = self.load_and_preprocess_data(csv_path)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Encode labels
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
            )
            
            # Train multiple models (CatBoost requires Rust, so using 3 models)
            algorithms = ['xgboost', 'lightgbm', 'randomforest']
            model_scores = {}
            
            for algorithm in algorithms:
                logger.info(f"Training {algorithm}...")
                
                if optimize and algorithm != 'randomforest':
                    best_params = self.optimize_hyperparameters(X_train, y_train, algorithm)
                else:
                    best_params = {}
                
                # Train model with best parameters
                if algorithm == 'xgboost':
                    model = xgb.XGBClassifier(**best_params)
                elif algorithm == 'lightgbm':
                    model = lgb.LGBMClassifier(**best_params)
                else:  # randomforest
                    model = RandomForestClassifier(n_estimators=200, random_state=42)
                
                # Train and evaluate
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                model_scores[algorithm] = accuracy
                self.models[algorithm] = model
                
                logger.info(f"{algorithm} accuracy: {accuracy:.4f}")
            
            # Select best model
            self.best_model_name = max(model_scores, key=model_scores.get)
            self.best_model = self.models[self.best_model_name]
            self.best_score = model_scores[self.best_model_name]
            
            logger.info(f"Best model: {self.best_model_name} with accuracy: {self.best_score:.4f}")
            
            # Save models and artifacts
            self._save_models()
            
            return model_scores
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            raise
    
    def _save_models(self):
        """Save trained models and preprocessing artifacts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save best model
        joblib.dump(self.best_model, os.path.join(self.model_dir, f"best_model_{timestamp}.joblib"))
        joblib.dump(self.scaler, os.path.join(self.model_dir, "scaler.joblib"))
        joblib.dump(self.label_encoder, os.path.join(self.model_dir, "label_encoder.joblib"))
        
        # Save metadata
        metadata = {
            "model_name": self.best_model_name,
            "accuracy": self.best_score,
            "feature_names": self.feature_names,
            "timestamp": timestamp,
            "version": "2.0"
        }
        
        with open(os.path.join(self.model_dir, "model_metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Models saved to {self.model_dir}")
    
    def load_models(self):
        """Load pre-trained models and artifacts"""
        try:
            # Load metadata
            with open(os.path.join(self.model_dir, "model_metadata.json"), 'r') as f:
                metadata = json.load(f)
            
            # Load best model
            model_files = [f for f in os.listdir(self.model_dir) if f.startswith("best_model_")]
            if not model_files:
                raise FileNotFoundError("No trained models found")
            
            latest_model = sorted(model_files)[-1]
            self.best_model = joblib.load(os.path.join(self.model_dir, latest_model))
            self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.joblib"))
            self.label_encoder = joblib.load(os.path.join(self.model_dir, "label_encoder.joblib"))
            
            # Set model attributes from metadata
            self.best_model_name = metadata['model_name']
            self.best_score = metadata['accuracy']
            
            logger.info(f"Loaded model: {metadata['model_name']} (accuracy: {metadata['accuracy']:.4f})")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def predict_crop(self, n: float, p: float, k: float, ph: float,
                    lat: float = None, lon: float = None) -> Dict[str, Any]:
        """Predict crop recommendation with enhanced features"""
        try:
            # Get weather data
            if lat is None or lon is None:
                lat, lon = self.get_location_by_ip()
            
            weather = self.fetch_weather_data(lat, lon)
            
            # Prepare features
            features = np.array([[
                n, p, k, weather['temperature'], weather['humidity'], ph, weather['rainfall']
            ]])
            
            # Add engineered features
            n_p_ratio = n / (p + 1e-8)
            n_k_ratio = n / (k + 1e-8)
            p_k_ratio = p / (k + 1e-8)
            temp_humidity = weather['temperature'] * weather['humidity']
            temp_rainfall = weather['temperature'] * weather['rainfall']
            soil_quality = (n + p + k) / 3
            
            enhanced_features = np.array([[
                n, p, k, weather['temperature'], weather['humidity'], ph, weather['rainfall'],
                n_p_ratio, n_k_ratio, p_k_ratio, temp_humidity, temp_rainfall, soil_quality
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(enhanced_features)
            
            # Make prediction
            prediction = self.best_model.predict(features_scaled)[0]
            predicted_crop = self.label_encoder.inverse_transform([prediction])[0]
            
            # Get probabilities for all crops
            probabilities = self.best_model.predict_proba(features_scaled)[0]
            crop_probs = {
                crop: float(prob) for crop, prob in 
                zip(self.label_encoder.classes_, probabilities)
            }
            
            # Get top 3 alternative crops
            sorted_crops = sorted(crop_probs.items(), key=lambda x: x[1], reverse=True)
            alternatives = [crop for crop, prob in sorted_crops[1:4]]
            
            return {
                "predicted_crop": predicted_crop,
                "confidence_score": float(max(probabilities)),
                "probabilities": crop_probs,
                "alternative_crops": alternatives,
                "used_features": {
                    "N": n, "P": p, "K": k, "ph": ph,
                    "temperature": weather['temperature'],
                    "humidity": weather['humidity'],
                    "rainfall": weather['rainfall'],
                    "latitude": lat, "longitude": lon
                },
                "model_info": {
                    "model_name": self.best_model_name,
                    "accuracy": self.best_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            raise


# Global instance with proper initialization
crop_recommender = OptimizedCropRecommender(
    model_dir="./crop_models/",
    openweather_api_key="653c5d05ceab43cbae5e146f96e62499"
)
