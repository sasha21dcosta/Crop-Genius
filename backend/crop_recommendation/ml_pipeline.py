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
        
        # Comprehensive crop information database
        self.crop_database = self._initialize_crop_database()
        
    def _initialize_crop_database(self) -> Dict[str, Dict[str, str]]:
        """Initialize comprehensive crop information database"""
        return {
            "rice": {
                "ideal_temp": "25–35°C",
                "ideal_rainfall": "100–200mm",
                "yield": "2500–3500 kg/ha",
                "reason": "High rainfall and warm climate favor rice cultivation with adequate water supply.",
                "suggestion": "Maintain flooded soil conditions, transplant uniformly spaced seedlings, and apply nitrogen in split doses.",
                "season": "Kharif (Monsoon)",
                "duration": "120-150 days"
            },
            "maize": {
                "ideal_temp": "18–27°C",
                "ideal_rainfall": "50–100mm",
                "yield": "3000–4000 kg/ha",
                "reason": "Balanced nutrients and moderate rainfall suit maize growth with good drainage.",
                "suggestion": "Maintain soil moisture, apply nitrogen during early growth stages, and ensure proper spacing.",
                "season": "Kharif & Rabi",
                "duration": "80-110 days"
            },
            "chickpea": {
                "ideal_temp": "20–30°C",
                "ideal_rainfall": "60–100mm",
                "yield": "800–1200 kg/ha",
                "reason": "Cool season crop requiring moderate moisture and well-drained soil.",
                "suggestion": "Sow after monsoon, apply phosphorus fertilizer, and control pod borer pests.",
                "season": "Rabi (Winter)",
                "duration": "100-120 days"
            },
            "kidneybeans": {
                "ideal_temp": "15–25°C",
                "ideal_rainfall": "75–125mm",
                "yield": "1500–2000 kg/ha",
                "reason": "Prefers cool climate with moderate rainfall and loamy soil.",
                "suggestion": "Provide support stakes, ensure good drainage, and avoid waterlogging.",
                "season": "Rabi",
                "duration": "90-120 days"
            },
            "pigeonpea": {
                "ideal_temp": "20–30°C",
                "ideal_rainfall": "60–100mm",
                "yield": "700–1000 kg/ha",
                "reason": "Drought-tolerant crop suited for semi-arid regions with low to moderate rainfall.",
                "suggestion": "Plant during monsoon, requires minimal irrigation, and fix nitrogen naturally.",
                "season": "Kharif",
                "duration": "150-180 days"
            },
            "mothbeans": {
                "ideal_temp": "25–35°C",
                "ideal_rainfall": "40–60mm",
                "yield": "300–500 kg/ha",
                "reason": "Highly drought-tolerant, suitable for arid zones with low rainfall.",
                "suggestion": "Sow after first monsoon shower, requires minimal care and fertilizer.",
                "season": "Kharif",
                "duration": "75-90 days"
            },
            "mungbean": {
                "ideal_temp": "25–35°C",
                "ideal_rainfall": "60–90mm",
                "yield": "500–800 kg/ha",
                "reason": "Short duration crop suitable for warm climate with moderate water needs.",
                "suggestion": "Can be grown between two main crops, apply minimal nitrogen, and harvest timely.",
                "season": "Kharif & Zaid",
                "duration": "60-70 days"
            },
            "blackgram": {
                "ideal_temp": "25–35°C",
                "ideal_rainfall": "60–100mm",
                "yield": "500–800 kg/ha",
                "reason": "Warm season pulse crop with moderate water requirements.",
                "suggestion": "Sow at the onset of monsoon, apply phosphorus, and control yellow mosaic virus.",
                "season": "Kharif",
                "duration": "70-90 days"
            },
            "lentil": {
                "ideal_temp": "18–25°C",
                "ideal_rainfall": "50–80mm",
                "yield": "700–1000 kg/ha",
                "reason": "Cool season crop requiring well-drained soil and moderate moisture.",
                "suggestion": "Sow in late October, avoid excess nitrogen, and harvest when pods turn brown.",
                "season": "Rabi",
                "duration": "110-130 days"
            },
            "pomegranate": {
                "ideal_temp": "25–35°C",
                "ideal_rainfall": "50–100mm",
                "yield": "10–15 tons/ha",
                "reason": "Semi-arid climate fruit crop tolerant to drought and heat.",
                "suggestion": "Prune regularly, provide drip irrigation, and control fruit borer pests.",
                "season": "Year-round",
                "duration": "Perennial"
            },
            "banana": {
                "ideal_temp": "26–30°C",
                "ideal_rainfall": "100–150mm",
                "yield": "40–60 tons/ha",
                "reason": "Hot and humid tropical conditions support rapid banana growth.",
                "suggestion": "Provide regular irrigation, apply potassium fertilizer monthly, and remove suckers.",
                "season": "Year-round",
                "duration": "10-12 months"
            },
            "mango": {
                "ideal_temp": "24–30°C",
                "ideal_rainfall": "75–250mm",
                "yield": "10–20 tons/ha",
                "reason": "Tropical climate with moderate rainfall suits mango flowering and fruiting.",
                "suggestion": "Irrigate young trees, prune annually, and apply NPK fertilizer before flowering.",
                "season": "Year-round (fruits in summer)",
                "duration": "Perennial"
            },
            "grapes": {
                "ideal_temp": "20–30°C",
                "ideal_rainfall": "50–100mm",
                "yield": "20–25 tons/ha",
                "reason": "Dry and warm climate supports grape quality and sugar content development.",
                "suggestion": "Provide trellis support, regulate pruning cycles, and ensure good air circulation.",
                "season": "Year-round",
                "duration": "Perennial"
            },
            "watermelon": {
                "ideal_temp": "25–30°C",
                "ideal_rainfall": "50–75mm",
                "yield": "25–35 tons/ha",
                "reason": "Warm climate with moderate rainfall supports fruit development.",
                "suggestion": "Provide well-drained sandy loam soil, regular irrigation during fruiting, and mulching.",
                "season": "Summer",
                "duration": "80-90 days"
            },
            "muskmelon": {
                "ideal_temp": "25–30°C",
                "ideal_rainfall": "50–75mm",
                "yield": "15–25 tons/ha",
                "reason": "Warm climate with moderate rainfall supports muskmelon sweetness.",
                "suggestion": "Ensure good drainage, regular irrigation during fruiting, and protect from heavy rains.",
                "season": "Summer",
                "duration": "90-100 days"
            },
            "apple": {
                "ideal_temp": "18–24°C",
                "ideal_rainfall": "100–200mm",
                "yield": "10–15 tons/ha",
                "reason": "Cool temperate climate and moderate rainfall favor apple growth and quality.",
                "suggestion": "Plant on hilly slopes, prune trees annually, and apply balanced fertilizers.",
                "season": "Year-round (fruits in autumn)",
                "duration": "Perennial"
            },
            "orange": {
                "ideal_temp": "20–30°C",
                "ideal_rainfall": "100–200mm",
                "yield": "15–25 tons/ha",
                "reason": "Subtropical climate with moderate rainfall supports citrus fruit development.",
                "suggestion": "Maintain soil pH 6-7, provide regular irrigation, and control citrus canker.",
                "season": "Year-round",
                "duration": "Perennial"
            },
            "papaya": {
                "ideal_temp": "25–30°C",
                "ideal_rainfall": "100–150mm",
                "yield": "40–60 tons/ha",
                "reason": "Warm tropical climate with moderate rainfall favors continuous papaya fruiting.",
                "suggestion": "Ensure well-drained soil, control aphid infestations, and remove male plants.",
                "season": "Year-round",
                "duration": "8-10 months"
            },
            "coconut": {
                "ideal_temp": "27–32°C",
                "ideal_rainfall": "150–250mm",
                "yield": "60–80 nuts per tree",
                "reason": "Hot and humid coastal climate with high rainfall suits coconut palms.",
                "suggestion": "Plant in well-drained soil, apply organic manure, and ensure regular watering.",
                "season": "Year-round",
                "duration": "Perennial"
            },
            "cotton": {
                "ideal_temp": "21–30°C",
                "ideal_rainfall": "50–100mm",
                "yield": "1500–2000 kg/ha",
                "reason": "Moderate rainfall and warm temperature with black soil support cotton fiber development.",
                "suggestion": "Avoid excess irrigation, manage bollworm pests, and pick cotton at right maturity.",
                "season": "Kharif",
                "duration": "150-180 days"
            },
            "jute": {
                "ideal_temp": "25–35°C",
                "ideal_rainfall": "150–250mm",
                "yield": "2000–2500 kg/ha",
                "reason": "High humidity and heavy rainfall support jute fiber growth in alluvial soil.",
                "suggestion": "Sow during monsoon, apply nitrogen fertilizer, and ret fibers properly.",
                "season": "Kharif",
                "duration": "120-150 days"
            },
            "coffee": {
                "ideal_temp": "15–28°C",
                "ideal_rainfall": "150–250mm",
                "yield": "800–2500 kg/ha",
                "reason": "Cool temperature with high rainfall and shaded conditions support coffee beans.",
                "suggestion": "Provide shade trees, avoid waterlogging, and harvest cherries when fully ripe.",
                "season": "Year-round",
                "duration": "Perennial"
            }
        }
    
    def analyze_nutrient(self, value: float, low: float, high: float, nutrient: str) -> Dict[str, str]:
        """Analyze nutrient levels and provide recommendations"""
        if value < low:
            recommendations = {
                "N": {
                    "status": "Low",
                    "recommendation": "Add urea (46-0-0) or ammonium sulfate (21-0-0)",
                    "quantity": f"Apply 50-100 kg/ha of urea",
                    "timing": "Split application: 1/3 at sowing, 1/3 at vegetative stage, 1/3 at flowering"
                },
                "P": {
                    "status": "Low",
                    "recommendation": "Add single superphosphate (SSP) or di-ammonium phosphate (DAP)",
                    "quantity": f"Apply 100-150 kg/ha of DAP",
                    "timing": "Full dose as basal application at sowing"
                },
                "K": {
                    "status": "Low",
                    "recommendation": "Add muriate of potash (MOP) or sulfate of potash",
                    "quantity": f"Apply 50-75 kg/ha of MOP",
                    "timing": "Split application: Half at sowing, half at flowering"
                }
            }
            return recommendations[nutrient]
        elif value > high:
            recommendations = {
                "N": {
                    "status": "High",
                    "recommendation": "Avoid nitrogen fertilizer this season",
                    "quantity": "No additional nitrogen needed",
                    "timing": "Monitor soil after harvest"
                },
                "P": {
                    "status": "High",
                    "recommendation": "Avoid phosphate fertilizer this season",
                    "quantity": "No additional phosphorus needed",
                    "timing": "Test soil again next season"
                },
                "K": {
                    "status": "High",
                    "recommendation": "Avoid potash fertilizer this season",
                    "quantity": "No additional potassium needed",
                    "timing": "Natural depletion will occur"
                }
            }
            return recommendations[nutrient]
        else:
            return {
                "status": "Optimal",
                "recommendation": f"{nutrient} levels are in optimal range",
                "quantity": "Maintain current levels with balanced fertilization",
                "timing": "Regular soil testing recommended"
            }
    
    def get_location_by_ip(self) -> Tuple[float, float]:
        """Get approximate latitude and longitude based on public IP"""
        try:
            response = requests.get("https://ipinfo.io/json", timeout=5)
            data = response.json()
            print("=" * 60)
            print("🌍 LOCATION DETECTION")
            print("=" * 60)
            print(f"IP Info Response: {data}")
            loc = data.get("loc")
            if loc:
                lat, lon = map(float, loc.split(","))
                print(f"✅ Detected Location: Latitude={lat}, Longitude={lon}")
                print(f"   City: {data.get('city', 'Unknown')}")
                print(f"   Region: {data.get('region', 'Unknown')}")
                print(f"   Country: {data.get('country', 'Unknown')}")
                print("=" * 60)
                return lat, lon
        except Exception as e:
            logger.warning(f"Error detecting location: {e}")
            print(f"⚠️ Location detection failed: {e}")
        
        # Fallback to India coordinates
        print("⚠️ Using fallback coordinates: India (20.5937, 78.9629)")
        print("=" * 60)
        return 20.5937, 78.9629
    
    def fetch_weather_data(self, lat: float, lon: float) -> Dict[str, float]:
        """Fetch 14-day weather forecast and calculate averages"""
        print("\n" + "=" * 60)
        print("🌤️ WEATHER FORECAST FETCHING (14-Day Average)")
        print("=" * 60)
        print(f"Coordinates: Latitude={lat}, Longitude={lon}")
        
        if not self.openweather_api_key:
            logger.warning("No OpenWeather API key provided, using default values")
            print("⚠️ No API key found - using default values")
            print("   Temperature: 25.0°C")
            print("   Humidity: 70.0%")
            print("   Rainfall: 0.0 mm")
            print("=" * 60)
            return {"temperature": 25.0, "humidity": 70.0, "rainfall": 0.0}
        
        try:
            # Try One Call API 3.0 for extended forecast (8 days max on free tier)
            # Then fall back to 5-day forecast if needed
            onecall_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={self.openweather_api_key}&units=metric&exclude=current,minutely,hourly,alerts"
            
            print(f"Fetching 14-day forecast from OpenWeatherMap API...")
            
            # Try One Call API first (may require subscription)
            try:
                response = requests.get(onecall_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    daily_forecasts = data.get('daily', [])[:14]  # Get up to 14 days
                    
                    temps = []
                    humidities = []
                    rainfalls = []
                    
                    for day in daily_forecasts:
                        temps.append(day['temp']['day'])
                        humidities.append(day['humidity'])
                        rainfalls.append(day.get('rain', 0.0))
                    
                    avg_temp = sum(temps) / len(temps)
                    avg_humidity = sum(humidities) / len(humidities)
                    avg_rainfall = sum(rainfalls) / len(rainfalls)
                    
                    print(f"✅ Forecast data fetched successfully!")
                    print(f"   Days analyzed: {len(daily_forecasts)}")
                    print(f"   Average Temperature: {avg_temp:.2f}°C")
                    print(f"   Temperature Range: {min(temps):.2f}°C - {max(temps):.2f}°C")
                    print(f"   Average Humidity: {avg_humidity:.2f}%")
                    print(f"   Average Rainfall: {avg_rainfall:.2f} mm/day")
                    print(f"   Total Rainfall (14 days): {sum(rainfalls):.2f} mm")
                    print("=" * 60)
                    
                    return {
                        "temperature": avg_temp,
                        "humidity": avg_humidity,
                        "rainfall": avg_rainfall
                    }
            except Exception as e:
                print(f"⚠️ One Call API not available: {e}")
                print("   Falling back to 5-day forecast...")
            
            # Fallback to 5-day/3-hour forecast (free tier)
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.openweather_api_key}&units=metric"
            response = requests.get(forecast_url, timeout=10)
            data = response.json()
            
            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}: {data.get('message', 'Unknown error')}")
            
            # Process 5-day forecast (40 3-hour intervals)
            forecasts = data.get('list', [])
            
            # Group by day and calculate daily averages
            from datetime import datetime
            daily_data = {}
            
            for forecast in forecasts:
                date = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
                if date not in daily_data:
                    daily_data[date] = {'temps': [], 'humidities': [], 'rainfalls': []}
                
                daily_data[date]['temps'].append(forecast['main']['temp'])
                daily_data[date]['humidities'].append(forecast['main']['humidity'])
                rainfall = forecast.get('rain', {}).get('3h', 0.0)
                daily_data[date]['rainfalls'].append(rainfall / 3)  # Convert to mm/hour, then average
            
            # Calculate daily averages
            daily_temps = []
            daily_humidities = []
            daily_rainfalls = []
            
            for date, values in sorted(daily_data.items())[:14]:  # Take up to 14 days
                daily_temps.append(sum(values['temps']) / len(values['temps']))
                daily_humidities.append(sum(values['humidities']) / len(values['humidities']))
                daily_rainfalls.append(sum(values['rainfalls']) / len(values['rainfalls']))
            
            # Calculate overall averages
            avg_temp = sum(daily_temps) / len(daily_temps)
            avg_humidity = sum(daily_humidities) / len(daily_humidities)
            avg_rainfall = sum(daily_rainfalls) / len(daily_rainfalls)
            
            print(f"✅ Forecast data fetched successfully!")
            print(f"   Days analyzed: {len(daily_temps)} (limited by API)")
            print(f"   Average Temperature: {avg_temp:.2f}°C")
            print(f"   Temperature Range: {min(daily_temps):.2f}°C - {max(daily_temps):.2f}°C")
            print(f"   Average Humidity: {avg_humidity:.2f}%")
            print(f"   Average Rainfall: {avg_rainfall:.2f} mm/day")
            if len(daily_temps) < 14:
                print(f"   ⚠️ Note: Only {len(daily_temps)} days available (API limitation)")
            print("=" * 60)
            
            return {
                "temperature": avg_temp,
                "humidity": avg_humidity,
                "rainfall": avg_rainfall
            }
            
        except Exception as e:
            logger.warning(f"Error fetching weather data: {e}")
            print(f"⚠️ Weather fetch failed: {e}")
            print("   Using default values instead:")
            print("   Temperature: 25.0°C")
            print("   Humidity: 70.0%")
            print("   Rainfall: 0.0 mm")
            print("=" * 60)
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
        """
        Enhanced crop prediction with explanation, yield estimate, and farming suggestions
        """
        try:
            print("\n" + "=" * 60)
            print("🌱 ENHANCED CROP PREDICTION STARTED")
            print("=" * 60)
            print("USER INPUT:")
            print(f"   Nitrogen (N): {n}")
            print(f"   Phosphorus (P): {p}")
            print(f"   Potassium (K): {k}")
            print(f"   pH Level: {ph}")
            
            # Get weather data
            if lat is None or lon is None:
                print("\n📍 No coordinates provided - detecting location...")
                lat, lon = self.get_location_by_ip()
            else:
                print(f"\n📍 Using provided coordinates: {lat}, {lon}")
            
            weather = self.fetch_weather_data(lat, lon)
            
            temperature = weather['temperature']
            humidity = weather['humidity']
            rainfall = weather['rainfall']
            
            # Prepare features
            features = np.array([[
                n, p, k, temperature, humidity, ph, rainfall
            ]])
            
            # Add engineered features
            n_p_ratio = n / (p + 1e-8)
            n_k_ratio = n / (k + 1e-8)
            p_k_ratio = p / (k + 1e-8)
            temp_humidity = temperature * humidity
            temp_rainfall = temperature * rainfall
            soil_quality = (n + p + k) / 3
            
            enhanced_features = np.array([[
                n, p, k, temperature, humidity, ph, rainfall,
                n_p_ratio, n_k_ratio, p_k_ratio, temp_humidity, temp_rainfall, soil_quality
            ]])
            
            print("\n" + "=" * 60)
            print("🔧 ENGINEERED FEATURES")
            print("=" * 60)
            print("Base Features (7):")
            print(f"   N={n}, P={p}, K={k}")
            print(f"   Temperature (14-day avg)={temperature:.2f}°C")
            print(f"   Humidity (14-day avg)={humidity:.2f}%")
            print(f"   pH={ph}")
            print(f"   Rainfall (14-day avg)={rainfall:.2f}mm/day")
            print("\nAdditional Features (6):")
            print(f"   N/P Ratio: {n_p_ratio:.2f}")
            print(f"   N/K Ratio: {n_k_ratio:.2f}")
            print(f"   P/K Ratio: {p_k_ratio:.2f}")
            print(f"   Temp×Humidity: {temp_humidity:.2f}")
            print(f"   Temp×Rainfall: {temp_rainfall:.2f}")
            print(f"   Soil Quality: {soil_quality:.2f}")
            print("=" * 60)
            
            # Scale features
            features_scaled = self.scaler.transform(enhanced_features)
            
            # Make prediction
            print("\n🤖 Running ML prediction...")
            print(f"   Model: {self.best_model_name}")
            prediction = self.best_model.predict(features_scaled)[0]
            predicted_crop = self.label_encoder.inverse_transform([prediction])[0]
            
            # Get probabilities for all crops
            probabilities = self.best_model.predict_proba(features_scaled)[0]
            crop_probs = {
                crop: float(prob) for crop, prob in 
                zip(self.label_encoder.classes_, probabilities)
            }
            
            # Get top alternatives
            sorted_crops = sorted(crop_probs.items(), key=lambda x: x[1], reverse=True)
            alternatives = [crop for crop, prob in sorted_crops[1:4]]
            
            # ===== ENHANCED FEATURES =====
            
            # 1. Get crop-specific information
            crop_key = predicted_crop.lower()
            crop_info = self.crop_database.get(crop_key, {
                "ideal_temp": "Data unavailable",
                "ideal_rainfall": "Data unavailable",
                "yield": "Varies by region",
                "reason": "Crop information not available in database.",
                "suggestion": "Consult local agricultural extension office for guidance.",
                "season": "Varies",
                "duration": "Unknown"
            })
            
            # 2. Nutrient Analysis
            print("\n" + "=" * 60)
            print("🧪 NUTRIENT ANALYSIS")
            print("=" * 60)
            
            nutrient_analysis = {
                "N": self.analyze_nutrient(n, 50, 100, "N"),
                "P": self.analyze_nutrient(p, 35, 70, "P"),
                "K": self.analyze_nutrient(k, 35, 80, "K")
            }
            
            for nutrient, analysis in nutrient_analysis.items():
                print(f"\n{nutrient} ({nutrient_analysis[nutrient]['status']}):")
                print(f"   Current: {n if nutrient == 'N' else (p if nutrient == 'P' else k)}")
                print(f"   {analysis['recommendation']}")
                print(f"   Quantity: {analysis['quantity']}")
                print(f"   Timing: {analysis['timing']}")
            
            # 3. Yield Prediction (synthetic formula-based estimate)
            predicted_yield_value = (
                (n * 0.5) + (p * 0.3) + (k * 0.2) + 
                (rainfall * 0.1) + np.random.normal(0, 10)
            )
            predicted_yield_value = max(0, round(predicted_yield_value, 2))
            
            # 4. Detailed Explanation
            explanation = (
                f"The AI model predicted **{predicted_crop}** with {float(max(probabilities)) * 100:.1f}% confidence "
                f"because your current conditions (Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%, "
                f"Rainfall: {rainfall:.1f}mm, pH: {ph}) closely match the ideal growing environment of "
                f"{crop_info['ideal_temp']} temperature and {crop_info['ideal_rainfall']} rainfall. "
                f"{crop_info['reason']}"
            )
            
            # 5. Soil Quality Assessment
            soil_quality_status = "Excellent" if soil_quality > 80 else (
                "Good" if soil_quality > 60 else (
                    "Fair" if soil_quality > 40 else "Poor"
                )
            )
            
            # 6. pH Analysis
            ph_status = "Optimal" if 6.0 <= ph <= 7.5 else (
                "Slightly acidic" if ph < 6.0 else "Slightly alkaline"
            )
            ph_recommendation = ""
            if ph < 6.0:
                ph_recommendation = "Add lime to raise pH"
            elif ph > 7.5:
                ph_recommendation = "Add sulfur or organic matter to lower pH"
            else:
                ph_recommendation = "pH is optimal for most crops"
            
            print("\n" + "=" * 60)
            print("✅ ENHANCED PREDICTION RESULT")
            print("=" * 60)
            print(f"🏆 Predicted Crop: {predicted_crop}")
            print(f"📊 Confidence: {float(max(probabilities)) * 100:.2f}%")
            print(f"🌾 Expected Yield: {crop_info['yield']}")
            print(f"📅 Growing Season: {crop_info['season']}")
            print(f"⏱️ Duration: {crop_info['duration']}")
            print(f"\n💡 Recommendation: {crop_info['suggestion']}")
            print(f"\nTop 5 Alternative Crops:")
            for i, (crop, prob) in enumerate(sorted_crops[:5], 1):
                print(f"   {i}. {crop}: {prob * 100:.2f}%")
            print("=" * 60 + "\n")
            
            return {
                "predicted_crop": predicted_crop,
                "confidence_score": float(max(probabilities)),
                "probabilities": crop_probs,
                "alternative_crops": alternatives,
                
                # Enhanced Information
                "crop_information": {
                    "ideal_temperature": crop_info['ideal_temp'],
                    "ideal_rainfall": crop_info['ideal_rainfall'],
                    "expected_yield": crop_info['yield'],
                    "growing_season": crop_info['season'],
                    "duration": crop_info['duration']
                },
                
                "reason": crop_info['reason'],
                "farming_suggestion": crop_info['suggestion'],
                "detailed_explanation": explanation,
                
                "yield_prediction": {
                    "expected_yield_range": crop_info['yield'],
                    "predicted_yield_index": predicted_yield_value,
                    "note": "Yield index is a synthetic estimate based on soil nutrients and weather"
                },
                
                "nutrient_analysis": nutrient_analysis,
                
                "soil_assessment": {
                    "soil_quality_index": round(soil_quality, 2),
                    "soil_quality_status": soil_quality_status,
                    "ph_level": ph,
                    "ph_status": ph_status,
                    "ph_recommendation": ph_recommendation
                },
                
                "used_features": {
                    "N": n, "P": p, "K": k, "ph": ph,
                    "temperature": temperature,
                    "humidity": humidity,
                    "rainfall": rainfall,
                    "latitude": lat, "longitude": lon
                },
                
                "model_info": {
                    "model_name": self.best_model_name,
                    "accuracy": self.best_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            print(f"❌ ERROR: {e}")
            raise


# Global instance with proper initialization
crop_recommender = OptimizedCropRecommender(
    model_dir="./crop_models/",
    openweather_api_key="653c5d05ceab43cbae5e146f96e62499"
)
