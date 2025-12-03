from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Vehicle, Trip
from app.services.calculation_service import CalculationService
from datetime import datetime

trips_bp = Blueprint('trips', __name__, url_prefix='/api/trips')
calc = CalculationService()

@trips_bp.route('/start', methods=['POST'])
@jwt_required()
def start_trip():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    vehicle = Vehicle.query.filter_by(user_id=user_id, id=data.get('vehicle_id')).first()
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    
    trip = Trip(
        user_id=user_id,
        vehicle_id=vehicle.id,
        start_latitude=data.get('start_latitude'),
        start_longitude=data.get('start_longitude'),
        start_battery_percentage=data.get('start_battery', 100),
        temperature_celsius=data.get('temperature', 25),
        started_at=datetime.utcnow()
    )
    
    db.session.add(trip)
    db.session.commit()
    
    return jsonify({
        'message': 'Trip started',
        'trip_id': trip.id
    }), 201

@trips_bp.route('/<int:trip_id>/end', methods=['POST'])
@jwt_required()
def end_trip(trip_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
    
    # Calculate distance and CO2
    trip.end_latitude = data.get('end_latitude')
    trip.end_longitude = data.get('end_longitude')
    trip.end_battery_percentage = data.get('end_battery', 0)
    trip.completed_at = datetime.utcnow()
    
    # Calculate distance using Haversine
    import math
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    trip.distance_km = haversine(trip.start_latitude, trip.start_longitude, trip.end_latitude, trip.end_longitude)
    trip.duration_minutes = int((trip.completed_at - trip.started_at).total_seconds() / 60)
    
    # Calculate CO2 and energy
    trip.energy_consumed_kwh = trip.distance_km * trip.vehicle.efficiency_kwh_per_km
    trip.co2_generated_grams = calc.calculate_co2_generated(trip.distance_km, 700, trip.vehicle.efficiency_kwh_per_km)
    trip.co2_saved_vs_petrol_grams = calc.calculate_co2_saved(trip.distance_km)
    trip.eco_score = calc.calculate_eco_score(trip)
    
    # Update user
    user = User.query.get(user_id)
    user.total_trips += 1
    user.total_co2_saved += trip.co2_saved_vs_petrol_grams / 1000  # Convert to kg
    user.current_eco_score = trip.eco_score
    
    # Update battery health
    battery_degradation = (trip.start_battery_percentage - trip.end_battery_percentage) * 0.001
    trip.vehicle.current_battery_health = max(80.0, trip.vehicle.current_battery_health - battery_degradation)
    trip.vehicle.current_battery_percentage = trip.end_battery_percentage
    
    db.session.commit()
    
    return jsonify({
        'message': 'Trip completed',
        'trip': trip.to_dict(),
        'co2_saved_kg': round(trip.co2_saved_vs_petrol_grams / 1000, 2),
        'trees_equivalent': round((trip.co2_generated_grams / 1000) / 25, 2)
    }), 200

@trips_bp.route('', methods=['GET'])
@jwt_required()
def list_trips():
    user_id = get_jwt_identity()
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.created_at.desc()).limit(50).all()
    
    return jsonify([trip.to_dict() for trip in trips]), 200

@trips_bp.route('/<int:trip_id>', methods=['GET'])
@jwt_required()
def get_trip(trip_id):
    user_id = get_jwt_identity()
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()
    
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
    
    return jsonify(trip.to_dict()), 200
