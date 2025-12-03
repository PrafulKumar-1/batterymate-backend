from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.ml_service import MLService
from app.utils.logger import get_logger
from datetime import datetime

air_quality_bp = Blueprint('air_quality', __name__, url_prefix='/api/air-quality')
ml_service = MLService()
logger = get_logger(__name__)

@air_quality_bp.route('/current', methods=['GET'])
def get_current_air_quality():
    """Get current air quality (Mock Data)"""
    try:
        # Mock data for the dashboard
        return jsonify({
            'aqi': 85,
            'level': 'Moderate',
            'pm25': 42.5,
            'routes': [
                {'name': 'Via Western Express Hwy', 'aqi': 110},
                {'name': 'Via Link Road', 'aqi': 85},
                {'name': 'Via SV Road', 'aqi': 95}
            ]
        }), 200
    except Exception as e:
        logger.error(f"Error getting air quality: {e}")
        return jsonify({'error': str(e)}), 500

@air_quality_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict_air_quality():
    try:
        data = request.get_json()
        features = {
            'pm10': 68, 'no2': 35, 'o3': 50, 'humidity': 65,
            'wind_speed': 8.5, 'temperature': 22, 'cloud_cover': 40
        }
        pm25, level = ml_service.predict_air_quality(features)
        
        return jsonify({
            'pm25': round(pm25, 2),
            'air_quality_level': level,
            'timestamp': datetime.utcnow()
        }), 200
    except Exception as e:
        logger.error(f"Error predicting: {e}")
        return jsonify({'error': str(e)}), 500

@air_quality_bp.route('/compare-routes', methods=['POST'])
@jwt_required()
def compare_routes():
    try:
        data = request.get_json()
        routes = data.get('routes', [])
        evaluated_routes = []
        for route in routes:
            evaluated_routes.append({
                'id': route.get('id'),
                'avg_pm25': 45.0,
                'avg_aqi': 65,
                'recommendation': 'Moderate'
            })
        return jsonify({'routes': evaluated_routes}), 200
    except Exception as e:
        logger.error(f"Error comparing routes: {e}")
        return jsonify({'error': str(e)}), 500