from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services import CacheService
from app.utils.logger import get_logger
import requests
import os
from datetime import datetime

grid_carbon_bp = Blueprint('grid_carbon', __name__)
cache_service = CacheService()
logger = get_logger(__name__)

@grid_carbon_bp.route('/current', methods=['GET'])
def get_current_carbon_intensity():
    """Get current grid carbon intensity"""
    try:
        # Check cache
        cached = cache_service.get('grid_carbon_intensity')
        if cached:
            return jsonify(cached), 200
        
        # Mock data (replace with real API)
        intensity_data = {
            'carbon_intensity': 700,
            'renewable_percent': 25,
            'coal_percent': 55,
            'natural_gas_percent': 10,
            'solar_percent': 12,
            'wind_percent': 13,
            'hydro_percent': 5,
            'other_percent': 5,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 30 minutes
        cache_service.set('grid_carbon_intensity', intensity_data, ttl=1800)
        
        return jsonify(intensity_data), 200
    
    except Exception as e:
        logger.error(f"Error getting grid carbon intensity: {e}")
        return jsonify({'error': str(e)}), 500

@grid_carbon_bp.route('/forecast', methods=['GET'])
def get_carbon_forecast():
    """Get 24-hour carbon intensity forecast"""
    try:
        # Check cache
        cached = cache_service.get('carbon_forecast')
        if cached:
            return jsonify(cached), 200
        
        # Mock forecast
        forecast = {
            'hours': [
                {'hour': i, 'intensity': 700 + (i % 24) * 10}
                for i in range(24)
            ],
            'best_charging_hour': 14,  # Peak solar
            'worst_charging_hour': 8   # Peak coal
        }
        
        # Cache for 1 hour
        cache_service.set('carbon_forecast', forecast, ttl=3600)
        
        return jsonify(forecast), 200
    
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return jsonify({'error': str(e)}), 500
