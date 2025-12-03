import numpy as np
import tensorflow as tf
import pickle
import os
import logging

logger = logging.getLogger(__name__)

class RangePredictor:
    """LSTM model for battery range prediction - with graceful fallback"""
    
    def __init__(self):
        """Initialize model and scaler"""
        self.model = None
        self.features_scaler = None
        self.target_scaler = None
        self.model_available = False
        
        try:
            base_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'models')
            
            # Try to load model
            model_path = os.path.join(base_path, 'lstm_range_model.h5')
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                logger.info("✅ LSTM Range Model loaded")
                self.model_available = True
            else:
                logger.warning(f"⚠️ Model file not found: {model_path}")
                logger.warning("💡 Will use fallback calculations")
                
        except Exception as e:
            logger.warning(f"⚠️ Error loading Range Predictor: {e}")
            logger.warning("💡 Will use fallback calculations")
    
    def predict(self, features: dict):
        """
        Predict battery percentage at destination
        
        Args:
            features: {
                'current_battery': float (0-100),
                'temperature': float (celsius),
                'traffic': str ('low', 'medium', 'high'),
                'distance_km': float,
                'vehicle_age': int (years),
                'humidity': float (0-100),
                'wind_speed': float (km/h),
                'hour': int (0-23),
                'day_of_week': int (0-6)
            }
        
        Returns:
            (predicted_battery_percent, confidence)
        """
        
        if self.model_available and self.model:
            return self._predict_with_model(features)
        else:
            return self._predict_fallback(features)
    
    def _predict_with_model(self, features: dict):
        """Use actual ML model for prediction"""
        try:
            traffic_map = {'low': 0, 'medium': 1, 'high': 2}
            
            feature_array = np.array([[
                features['current_battery'],
                features['temperature'],
                traffic_map.get(features['traffic'], 1),
                features['distance_km'],
                features['vehicle_age'],
                features.get('humidity', 50),
                features.get('wind_speed', 5),
                features['hour'],
                features['day_of_week']
            ]], dtype=np.float32)
            
            sequence = feature_array.reshape(1, 1, -1)
            raw_prediction = self.model.predict(sequence, verbose=0)
            predicted_battery = np.clip(raw_prediction, 0, 100)
            
            confidence = 0.87
            if features['distance_km'] > 100:
                confidence *= 0.95
            if features['temperature'] < 0 or features['temperature'] > 40:
                confidence *= 0.85
            
            return (float(predicted_battery), float(confidence))
        
        except Exception as e:
            logger.warning(f"Model prediction failed: {e}, using fallback")
            return self._predict_fallback(features)
    
    @staticmethod
    def _predict_fallback(features: dict):
        """Fallback calculation when model unavailable"""
        current_battery = features['current_battery']
        distance_km = features['distance_km']
        temperature = features['temperature']
        battery_capacity = features.get('battery_capacity', 60.0)
        efficiency = features.get('efficiency', 0.14)
        
        # Calculate remaining battery using simple physics
        # Energy consumed = distance × efficiency
        energy_consumed_kwh = distance_km * efficiency
        
        # Battery percentage consumption
        # (energy_consumed / battery_capacity) × 100
        battery_consumption_percent = (energy_consumed_kwh / battery_capacity) * 100
        predicted_battery = current_battery - battery_consumption_percent
        
        # Temperature adjustment
        if temperature < 0:
            predicted_battery *= 0.85  # 15% less efficient in extreme cold
        elif temperature > 40:
            predicted_battery *= 0.90  # 10% less efficient in extreme heat
        
        # Clamp to valid range
        predicted_battery = np.clip(predicted_battery, 0, 100)
        
        # Lower confidence for fallback
        confidence = 0.70
        
        return (float(predicted_battery), float(confidence))
