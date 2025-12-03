import joblib
import os
import numpy as np
from typing import Dict, List

class ChargingOptimizer:
    """XGBoost model for charging cost optimization"""
    
    def __init__(self):
        """Initialize model"""
        base_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'models')
        
        self.model = joblib.load(
            os.path.join(base_path, 'xgboost_cost_model.pkl')
        )
    
    def predict_cost(self, features: Dict) -> float:
        """
        Predict charging cost
        
        Args:
            features: {
                'distance_km': float,
                'hour': int (0-23),
                'day_of_week': int (0-6),
                'is_peak_hour': int (0 or 1),
                'is_weekend': int (0 or 1),
                'traffic_level': int (0=low, 1=medium, 2=high),
                'avg_speed_kmh': float
            }
        
        Returns:
            estimated_cost (in rupees)
        """
        
        feature_array = np.array([[
            features['distance_km'],
            features['hour'],
            features['day_of_week'],
            features.get('is_peak_hour', 0),
            features.get('is_weekend', 0),
            features.get('traffic_level', 1),
            features['avg_speed_kmh']
        ]])
        
        cost = self.model.predict(feature_array)
        return float(np.clip(cost, 0, 1000))
    
    def find_optimal_charging_time(self, 
                                   current_hour: int,
                                   day_of_week: int,
                                   distance_km: float,
                                   grid_intensity: List[float]) -> int:
        """
        Find optimal charging hour based on cost and carbon intensity
        
        Args:
            current_hour: Current hour (0-23)
            day_of_week: Day of week (0-6)
            distance_km: Expected distance
            grid_intensity: Hourly grid carbon intensity (24 values)
        
        Returns:
            best_hour (0-23)
        """
        
        best_cost = float('inf')
        best_hour = current_hour
        
        # Check next 24 hours
        for hour_offset in range(24):
            check_hour = (current_hour + hour_offset) % 24
            check_day = day_of_week if hour_offset == 0 else (day_of_week + 1) % 7
            
            is_peak = 1 if check_hour in [7, 8, 17, 18, 19] else 0
            is_weekend = 1 if check_day in [5, 6] else 0
            
            cost = self.predict_cost({
                'distance_km': distance_km,
                'hour': check_hour,
                'day_of_week': check_day,
                'is_peak_hour': is_peak,
                'is_weekend': is_weekend,
                'traffic_level': 1,
                'avg_speed_kmh': 50
            })
            
            # Factor in grid carbon intensity
            if check_hour < len(grid_intensity):
                carbon_factor = grid_intensity[check_hour] / 700  # Normalize
                cost *= carbon_factor
            
            if cost < best_cost:
                best_cost = cost
                best_hour = check_hour
        
        return best_hour
