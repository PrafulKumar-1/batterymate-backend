from app import db, create_app
from app.models.user import Trip
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import math

routes_bp = Blueprint('routes', __name__, url_prefix='/api/routes')

@routes_bp.route('/directions', methods=['POST'])
@jwt_required()
def get_directions():
    """
    ✅ Generate detailed turn-by-turn directions
    """
    try:
        data = request.get_json()
        
        start_lat = float(data.get('start_latitude'))
        start_lon = float(data.get('start_longitude'))
        end_lat = float(data.get('end_latitude'))
        end_lon = float(data.get('end_longitude'))
        route_type = data.get('route_type', 'balanced')
        
        # Generate realistic waypoints
        waypoints = generate_waypoints(start_lat, start_lon, end_lat, end_lon, route_type)
        
        # Generate turn-by-turn directions
        directions = generate_turn_instructions(waypoints)
        
        return jsonify({
            'success': True,
            'waypoints': waypoints,
            'directions': directions,
            'total_distance': calculate_total_distance(waypoints),
            'estimated_time': estimate_time(waypoints)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_waypoints(start_lat, start_lon, end_lat, end_lon, route_type):
    """
    ✅ Generate realistic waypoints between start and end
    """
    waypoints = []
    
    # Start point
    waypoints.append({
        'lat': start_lat,
        'lon': start_lon,
        'type': 'start',
        'instruction': 'Start'
    })
    
    # Calculate intermediate points based on route type
    segments = 5 if route_type == 'balanced' else (7 if route_type == 'fastest' else 6)
    
    for i in range(1, segments):
        # Linear interpolation between start and end
        fraction = i / segments
        lat = start_lat + (end_lat - start_lat) * fraction
        lon = start_lon + (end_lon - start_lon) * fraction
        
        # Add slight variations for realism
        if i % 2 == 0:
            lat += 0.01
        else:
            lon += 0.01
        
        # Determine instruction based on position
        if i == 1:
            direction = get_cardinal_direction(start_lat, start_lon, lat, lon)
            instruction = f"Turn {direction} onto Main Highway"
        elif i == segments - 1:
            direction = get_cardinal_direction(start_lat, start_lon, end_lat, end_lon)
            instruction = f"Turn {direction} towards destination"
        else:
            instruction = f"Continue on Highway {100 + i}"
        
        waypoints.append({
            'lat': lat,
            'lon': lon,
            'type': 'waypoint',
            'instruction': instruction,
            'order': i
        })
    
    # End point
    waypoints.append({
        'lat': end_lat,
        'lon': end_lon,
        'type': 'end',
        'instruction': 'Destination reached'
    })
    
    return waypoints


def generate_turn_instructions(waypoints):
    """
    ✅ Generate detailed turn-by-turn instructions
    """
    instructions = []
    
    for i, wp in enumerate(waypoints):
        if wp['type'] == 'start':
            instructions.append({
                'step': i + 1,
                'instruction': f"📍 Start your journey",
                'distance': 0,
                'cumulative_distance': 0,
                'direction': 'Start'
            })
        
        elif wp['type'] == 'end':
            instructions.append({
                'step': i + 1,
                'instruction': f"🎯 You have arrived at your destination!",
                'distance': 0,
                'cumulative_distance': calculate_distance_to_waypoint(waypoints, i),
                'direction': 'End'
            })
        
        else:
            if i > 0:
                prev_wp = waypoints[i - 1]
                curr_wp = waypoints[i]
                
                # Calculate distance to this waypoint
                distance = haversine(prev_wp['lat'], prev_wp['lon'], curr_wp['lat'], curr_wp['lon'])
                
                # Get direction
                direction = get_cardinal_direction(prev_wp['lat'], prev_wp['lon'], curr_wp['lat'], curr_wp['lon'])
                
                instructions.append({
                    'step': i + 1,
                    'instruction': f"🛣️ {curr_wp.get('instruction', 'Continue')}",
                    'distance': round(distance, 2),
                    'cumulative_distance': round(calculate_distance_to_waypoint(waypoints, i), 2),
                    'direction': direction
                })
    
    return instructions


def get_cardinal_direction(lat1, lon1, lat2, lon2):
    """
    ✅ Get cardinal direction between two points
    """
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    angle = math.atan2(dlon, dlat) * 180 / math.pi
    
    if angle < 45 and angle >= -45:
        return "North"
    elif angle >= 45 and angle < 135:
        return "East"
    elif angle >= 135 or angle < -135:
        return "South"
    else:
        return "West"


def haversine(lat1, lon1, lat2, lon2):
    """
    ✅ Calculate distance between two GPS points
    """
    R = 6371  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def calculate_total_distance(waypoints):
    """
    ✅ Calculate total distance across all waypoints
    """
    total = 0
    for i in range(len(waypoints) - 1):
        curr = waypoints[i]
        next_wp = waypoints[i + 1]
        total += haversine(curr['lat'], curr['lon'], next_wp['lat'], next_wp['lon'])
    return round(total, 2)


def calculate_distance_to_waypoint(waypoints, index):
    """
    ✅ Calculate cumulative distance to a specific waypoint
    """
    total = 0
    for i in range(index):
        curr = waypoints[i]
        next_wp = waypoints[i + 1]
        total += haversine(curr['lat'], curr['lon'], next_wp['lat'], next_wp['lon'])
    return total


def estimate_time(waypoints):
    """
    ✅ Estimate travel time based on distance
    """
    total_distance = calculate_total_distance(waypoints)
    avg_speed = 60  # km/h average
    time_minutes = (total_distance / avg_speed) * 60
    return int(time_minutes)


@routes_bp.route('/nearby-charging', methods=['POST'])
@jwt_required()
def get_nearby_charging():
    """
    ✅ Get nearby charging stations along the route
    """
    try:
        data = request.get_json()
        
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        radius_km = float(data.get('radius', 50))
        
        # Simulated charging stations
        charging_stations = [
            {
                'id': 1,
                'name': 'EV Charging Hub - Downtown',
                'lat': latitude + 0.1,
                'lon': longitude + 0.1,
                'distance_km': 5,
                'plugs_available': 3,
                'average_rating': 4.8,
                'charging_time_mins': 30
            },
            {
                'id': 2,
                'name': 'Green Power Station',
                'lat': latitude - 0.05,
                'lon': longitude + 0.08,
                'distance_km': 8,
                'plugs_available': 2,
                'average_rating': 4.6,
                'charging_time_mins': 45
            },
            {
                'id': 3,
                'name': 'Quick Charge Express',
                'lat': latitude + 0.02,
                'lon': longitude - 0.1,
                'distance_km': 12,
                'plugs_available': 5,
                'average_rating': 4.9,
                'charging_time_mins': 25
            }
        ]
        
        return jsonify({
            'success': True,
            'stations': charging_stations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/traffic-info', methods=['POST'])
@jwt_required()
def get_traffic_info():
    """
    ✅ Get traffic information for the route
    """
    try:
        data = request.get_json()
        
        start_lat = float(data.get('start_latitude'))
        start_lon = float(data.get('start_longitude'))
        end_lat = float(data.get('end_latitude'))
        end_lon = float(data.get('end_longitude'))
        
        # Simulated traffic data
        traffic_info = {
            'current_conditions': 'Moderate',
            'congestion_level': 45,  # 0-100
            'average_speed': 55,  # km/h
            'estimated_delay': 10,  # minutes
            'alternative_routes': 2,
            'incidents': [
                {
                    'type': 'construction',
                    'location': 'Highway NH1 - Km 45',
                    'severity': 'moderate',
                    'duration': '2-3 hours'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'traffic': traffic_info
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500