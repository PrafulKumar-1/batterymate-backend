import logging
import os
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

class MLService:
    """ML Service with graceful fallback for missing models"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.models_available = False
        self.range_predictor = None
        self.air_quality_predictor = None
        
    def initialize(self):
        """Initialize ML models if available"""
        try:
            from app.ml_models.range_predictor import RangePredictor
            from app.ml_models.air_quality_predictor import AirQualityPredictor
            
            self.range_predictor = RangePredictor()
            self.air_quality_predictor = AirQualityPredictor()
            self.models_available = True
            logger.info("✅ ML models loaded successfully")
            
        except FileNotFoundError as e:
            logger.warning(f"⚠️ ML models not found: {e}")
            logger.warning("💡 Running in MOCK MODE - using default predictions")
            self.models_available = False
            
        except Exception as e:
            logger.warning(f"⚠️ Error loading ML models: {e}")
            logger.warning("💡 Running in MOCK MODE - using default predictions")
            self.models_available = False
    
    def predict_range(self, features: dict) -> tuple:
        """Predict battery range - with fallback to mock data"""
        if self.models_available and self.range_predictor:
            try:
                return self.range_predictor.predict(features)
            except Exception as e:
                logger.warning(f"Prediction error: {e}, using mock data")
        
        # FALLBACK: Mock prediction
        return self._mock_range_prediction(features)
    
    def predict_air_quality(self, features: dict) -> tuple:
        """Predict air quality - with fallback to mock data"""
        if self.models_available and self.air_quality_predictor:
            try:
                return self.air_quality_predictor.predict(features)
            except Exception as e:
                logger.warning(f"Air quality prediction error: {e}, using mock data")
        
        # FALLBACK: Mock prediction
        return self._mock_air_quality_prediction(features)
    
    @staticmethod
    def _mock_range_prediction(features: dict) -> tuple:
        """Mock range prediction when models unavailable"""
        distance_km = features.get('distance_km', 50)
        current_battery = features.get('current_battery', 100)
        
        # Simple calculation: assume 0.14 kWh/km efficiency
        max_range = (features.get('battery_capacity', 60) / 0.14)
        predicted_battery = max(0, current_battery - (distance_km / max_range * 100))
        
        # Adjust for temperature
        temp = features.get('temperature', 25)
        if temp < 0:
            predicted_battery *= 0.85  # 15% reduction in cold
        elif temp > 40:
            predicted_battery *= 0.90  # 10% reduction in heat
        
        confidence = 0.75  # Lower confidence for mock data
        return (float(predicted_battery), float(confidence))
    
    @staticmethod
    def _mock_air_quality_prediction(features: dict) -> tuple:
        """Mock air quality prediction when models unavailable"""
        # Default to moderate air quality
        pm25 = 50.0  # µg/m³ (moderate)
        aqi_level = "MODERATE"
        return (float(pm25), aqi_level)

# Initialize as singleton
ml_service = MLService()
