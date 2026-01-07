from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Vehicle, Trip
from app.services.calculation_service import CalculationService
from datetime import datetime
import math

trips_bp = Blueprint('trips', __name__, url_prefix='/api/trips')

calc = CalculationService()


# ==================== SAVE TRIP (NEW ENDPOINT) ====================
@trips_bp.route('/save', methods=['POST', 'OPTIONS'])
@jwt_required()
def save_trip():
    """Save a trip to history after navigation completes"""
    if request.method == 'OPTIONS':
        return '', 200
    
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        # Get values from request
        start_location = data.get('start_location', 'Unknown')
        end_location = data.get('end_location', 'Unknown')
        distance_km = float(data.get('distance_km', 0))
        duration_minutes = int(data.get('duration_minutes', 0))
        co2_saved_grams = float(data.get('co2_saved_grams', 0))
        eco_score = int(data.get('eco_score', 0))
        
        # Validation - at least some data
        if distance_km == 0 and duration_minutes == 0:
            return jsonify({
                'error': 'Invalid trip data',
                'message': 'Trip must have distance or duration'
            }), 400

        # Create trip record
        trip = Trip(
            user_id=user_id,
            start_location=start_location,
            end_location=end_location,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            co2_saved_vs_petrol_grams=co2_saved_grams,  # Use correct field name
            eco_score=eco_score,
            created_at=datetime.utcnow()
        )

        # Add to database
        db.session.add(trip)
        db.session.commit()

        # Update user stats
        user = User.query.get(user_id)
        if user:
            user.total_trips = (user.total_trips or 0) + 1
            user.total_co2_saved = (user.total_co2_saved or 0) + (co2_saved_grams / 1000)  # Convert to kg
            user.current_eco_score = eco_score
            db.session.commit()

        return jsonify({
            'message': 'Trip saved successfully',
            'trip_id': trip.id,
            'user_stats': {
                'total_trips': user.total_trips,
                'total_co2_saved_kg': round(user.total_co2_saved, 2),
                'current_eco_score': user.current_eco_score
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()  # Print full error
        return jsonify({
            'error': str(e),
            'message': 'Failed to save trip'
        }), 500





@trips_bp.route('/start', methods=['POST'])
@jwt_required()
def start_trip():
    """Start a new trip"""
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


# ==================== END TRIP ====================
@trips_bp.route('/<int:trip_id>/end', methods=['POST'])
@jwt_required()
def end_trip(trip_id):
    """Complete a trip with final location and battery"""
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
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    trip.distance_km = haversine(trip.start_latitude, trip.start_longitude, trip.end_latitude, trip.end_longitude)
    trip.duration_minutes = int((trip.completed_at - trip.started_at).total_seconds() / 60)

    # Calculate CO2 and energy
    if trip.vehicle:
        trip.energy_consumed_kwh = trip.distance_km * trip.vehicle.efficiency_kwh_per_km
        trip.co2_generated_grams = calc.calculate_co2_generated(trip.distance_km, 700, trip.vehicle.efficiency_kwh_per_km)
        trip.co2_saved_vs_petrol_grams = calc.calculate_co2_saved(trip.distance_km)
        trip.eco_score = calc.calculate_eco_score(trip)

        # Update battery health
        battery_degradation = (trip.start_battery_percentage - trip.end_battery_percentage) * 0.001
        trip.vehicle.current_battery_health = max(80.0, trip.vehicle.current_battery_health - battery_degradation)
        trip.vehicle.current_battery_percentage = trip.end_battery_percentage

    # Update user
    user = User.query.get(user_id)
    user.total_trips = (user.total_trips or 0) + 1
    user.total_co2_saved = (user.total_co2_saved or 0) + (trip.co2_saved_vs_petrol_grams / 1000)
    user.current_eco_score = trip.eco_score

    db.session.commit()

    return jsonify({
        'message': 'Trip completed',
        'trip': trip.to_dict(),
        'co2_saved_kg': round(trip.co2_saved_vs_petrol_grams / 1000, 2),
        'trees_equivalent': round((trip.co2_generated_grams / 1000) / 25, 2)
    }), 200


# ==================== LIST ALL TRIPS ====================
@trips_bp.route('', methods=['GET'])
@jwt_required()
def list_trips():
    """Get all trips for current user"""
    user_id = get_jwt_identity()
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.created_at.desc()).limit(50).all()

    return jsonify([trip.to_dict() for trip in trips]), 200


# ==================== GET SINGLE TRIP ====================
@trips_bp.route('/<int:trip_id>', methods=['GET'])
@jwt_required()
def get_trip(trip_id):
    """Get a specific trip"""
    user_id = get_jwt_identity()
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()

    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    return jsonify(trip.to_dict()), 200


# ==================== DELETE TRIP ====================
@trips_bp.route('/<int:trip_id>', methods=['DELETE'])
@jwt_required()
def delete_trip(trip_id):
    """Delete a trip"""
    user_id = get_jwt_identity()
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()

    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    db.session.delete(trip)
    db.session.commit()

    return jsonify({'message': 'Trip deleted successfully'}), 200


# ==================== GET TRIP STATS ====================
@trips_bp.route('/stats/summary', methods=['GET'])
@jwt_required()
def get_trip_stats():
    """Get aggregate trip statistics for user"""
    user_id = get_jwt_identity()

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    trips = Trip.query.filter_by(user_id=user_id).all()

    total_distance = sum([trip.distance_km for trip in trips if trip.distance_km])
    total_duration = sum([trip.duration_minutes for trip in trips if trip.duration_minutes])
    total_co2_saved = sum([trip.co2_saved_vs_petrol_grams for trip in trips if trip.co2_saved_vs_petrol_grams])

    return jsonify({
        'total_trips': len(trips),
        'total_distance_km': round(total_distance, 2),
        'total_duration_minutes': total_duration,
        'total_co2_saved_kg': round(total_co2_saved / 1000, 2),
        'average_eco_score': round(sum([trip.eco_score for trip in trips if trip.eco_score]) / max(len(trips), 1), 1),
        'user_eco_score': user.current_eco_score
    }), 200
