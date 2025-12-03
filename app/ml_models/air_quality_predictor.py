import numpy as np
import logging

logger = logging.getLogger(__name__)

class AirQualityPredictor:
    """LSTM model for air quality prediction - with graceful fallback"""
    
    def __init__(self):
        """Initialize model"""
        self.model = None
        self.model_available = False
        
        try:
            import tensorflow as tf
            import os
            
            base_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'models')
            model_path = os.path.join(base_path, 'lstm_air_quality_model.h5')
            
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                logger.info("✅ LSTM Air Quality Model loaded")
                self.model_available = True
            else:
                logger.warning(f"⚠️ Air Quality model not found: {model_path}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error loading Air Quality Predictor: {e}")
    
    def predict(self, features: dict):
        """
        Predict PM2.5 levels
        
        Args:
            features: {
                'pm10': float,
                'no2': float,
                'o3': float,
                'humidity': float (0-100),
                'wind_speed': float,
                'temperature': float,
                'cloud_cover': float (0-100)
            }
        
        Returns:
            (pm25_prediction, air_quality_level)
        """
        
        if self.model_available and self.model:
            return self._predict_with_model(features)
        else:
            return self._predict_fallback(features)
    
    def _predict_with_model(self, features: dict):
        """Use actual ML model"""
        try:
            feature_array = np.array([[
                features['pm10'],
                features['no2'],
                features['o3'],
                features['humidity'],
                features['wind_speed'],
                features['temperature'],
                features['cloud_cover']
            ]], dtype=np.float32)
            
            sequence = feature_array.reshape(1, 1, -1)
            raw_prediction = self.model.predict(sequence, verbose=0)
            pm25 = np.clip(raw_prediction, 0, 500)
            
            # Classify
            if pm25 <= 12:
                level = "GOOD"
            elif pm25 <= 35:
                level = "MODERATE"
            elif pm25 <= 55:
                level = "UNHEALTHY_FOR_SENSITIVE"
            elif pm25 <= 150:
                level = "UNHEALTHY"
            else:
                level = "HAZARDOUS"
            
            return (float(pm25), level)
        
        except Exception as e:
            logger.warning(f"Model prediction failed: {e}, using fallback")
            return self._predict_fallback(features)
    
    @staticmethod
    def _predict_fallback(features: dict):
        """Fallback calculation"""
        # Use PM10 as basis (rough estimate: PM2.5 ≈ 0.5 × PM10)
        pm10 = features.get('pm10', 50)
        pm25 = pm10 * 0.4  # Rough conversion
        
        # Adjust for wind (higher wind = cleaner air)
        wind_speed = features.get('wind_speed', 5)
        if wind_speed > 10:
            pm25 *= 0.8
        
        pm25 = np.clip(pm25, 0, 500)
        
        # Classify
        if pm25 <= 12:
            level = "GOOD"
        elif pm25 <= 35:
            level = "MODERATE"
        elif pm25 <= 55:
            level = "UNHEALTHY_FOR_SENSITIVE"
        elif pm25 <= 150:
            level = "UNHEALTHY"
        else:
            level = "HAZARDOUS"
        
        return (float(pm25), level)
