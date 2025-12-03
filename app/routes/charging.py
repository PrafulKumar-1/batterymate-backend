from flask import Blueprint, request, jsonify

charging_bp = Blueprint('charging', __name__, url_prefix='/api/charging')

@charging_bp.route('/stations', methods=['GET'])
def get_stations():
    # FIX: Removed 'station_id' argument that was causing the 500 error
    latitude = request.args.get('latitude', 19.0760)
    longitude = request.args.get('longitude', 72.8777)
    radius_km = request.args.get('radius', 10)
    
    # Mock charging stations data
    stations = [
        {
            'id': 1,
            'name': 'Premium EV Hub - Andheri',
            'latitude': 19.1136,
            'longitude': 72.8697,
            'distance_km': 2.5,
            'power_kw': 150,
            'available_chargers': 3,
            'total_chargers': 5,
            'cost_per_kwh': 15,
            'rating': 4.8,
            'average_wait_time': 10,
            'address': 'Andheri West, Mumbai',
            'charging_speed': 'Fast',
            'available_slots': 3,
            'total_slots': 5,
            'cost_per_hour': 150
        },
        {
            'id': 2,
            'name': 'Fast Charging - Bandra',
            'latitude': 19.0596,
            'longitude': 72.8295,
            'distance_km': 5.2,
            'power_kw': 50,
            'available_chargers': 1,
            'total_chargers': 3,
            'cost_per_kwh': 12,
            'rating': 4.5,
            'average_wait_time': 25,
            'address': 'Bandra Kurla Complex',
            'charging_speed': 'Standard',
            'available_slots': 1,
            'total_slots': 3,
            'cost_per_hour': 100
        },
        {
            'id': 3,
            'name': 'Eco Charging - Colaba',
            'latitude': 18.9676,
            'longitude': 72.8239,
            'distance_km': 8.1,
            'power_kw': 120,
            'available_chargers': 5,
            'total_chargers': 6,
            'cost_per_kwh': 14,
            'rating': 4.9,
            'average_wait_time': 5,
            'address': 'Colaba Causeway',
            'charging_speed': 'Fast',
            'available_slots': 5,
            'total_slots': 6,
            'cost_per_hour': 140
        }
    ]
    
    return jsonify(stations), 200

@charging_bp.route('/<int:station_id>/status', methods=['GET'])
def station_status(station_id):
    statuses = {
        1: {'available': 3, 'occupied': 2, 'out_of_service': 0, 'estimated_wait': 10},
        2: {'available': 1, 'occupied': 2, 'out_of_service': 0, 'estimated_wait': 25},
        3: {'available': 5, 'occupied': 1, 'out_of_service': 0, 'estimated_wait': 5}
    }
    
    status = statuses.get(station_id, {'available': 0, 'occupied': 0})
    
    return jsonify({
        'station_id': station_id,
        'available_chargers': status.get('available', 0),
        'occupied_chargers': status.get('occupied', 0),
        'estimated_wait_time_minutes': status.get('estimated_wait', 0),
        'updated_at': '2024-01-15T10:30:00Z'
    }), 200