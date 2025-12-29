from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Trip, EcoScore
from app.utils.logger import get_logger
from sqlalchemy import func, desc
from datetime import datetime

logger = get_logger(__name__)
eco_score_bp = Blueprint('eco_score', __name__, url_prefix='/api/eco-score')

@eco_score_bp.route('/leaderboard', methods=['GET'])
@jwt_required(optional=True)
def get_leaderboard():
    try:
        category = request.args.get('category', 'eco-score').lower()
        limit = min(int(request.args.get('limit', 100)), 500)
        page = max(int(request.args.get('page', 1)), 1)
        offset = (page - 1) * limit

        leaderboard_query = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.current_eco_score,
            func.count(Trip.id).label('trips_count'),
            func.coalesce(func.sum(Trip.distance_km), 0.0).label('distance_km'),
            func.coalesce(func.sum(Trip.co2_saved_vs_petrol_grams), 0.0).label('co2_saved_grams'),
            func.coalesce(func.sum(Trip.co2_saved_vs_petrol_grams) / 1000.0, 0.0).label('co2_saved_kg')
        ).outerjoin(
            Trip, User.id == Trip.user_id
        ).group_by(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.current_eco_score
        )

        if category == 'distance':
            leaderboard_query = leaderboard_query.order_by(desc('distance_km'))
        elif category == 'co2-saved':
            leaderboard_query = leaderboard_query.order_by(desc('co2_saved_grams'))
        elif category == 'trips':
            leaderboard_query = leaderboard_query.order_by(desc('trips_count'))
        else:
            leaderboard_query = leaderboard_query.order_by(
                desc(func.coalesce(func.sum(Trip.co2_saved_vs_petrol_grams) / func.nullif(func.sum(Trip.distance_km), 0), 0))
            )
        
        total_count = leaderboard_query.count()
        leaderboard_data = leaderboard_query.limit(limit).offset(offset).all()

        result = []
        for rank, user_data in enumerate(leaderboard_data, start=offset + 1):
            trips_count = int(user_data.trips_count or 0)
            distance_km = float(user_data.distance_km or 0)
            co2_saved_grams = float(user_data.co2_saved_grams or 0)
            co2_saved_kg = float(user_data.co2_saved_kg or 0)
            
            # Calculate eco_score from trips data
            if trips_count > 0 and distance_km > 0:
                eco_score_val = min(100, (co2_saved_grams / distance_km) / 100 * 100)
            else:
                eco_score_val = float(user_data.current_eco_score or 0)
            
            full_name = f"{user_data.first_name or ''} {user_data.last_name or ''}".strip() or 'Anonymous User'
            
            result.append({
                'rank': rank,
                'id': user_data.id,
                'name': full_name,
                'email': user_data.email or '',
                'vehicle_model': 'Electric Vehicle',
                'eco_score': round(eco_score_val, 2),
                'trips_count': trips_count,
                'distance_km': round(distance_km, 2),
                'co2_saved': round(co2_saved_kg, 2),
                'co2_saved_grams': round(co2_saved_grams, 0),
                'trees_equivalent': max(1, round(co2_saved_kg / 20)) if co2_saved_kg > 0 else 0,
                'level': get_level_from_score(eco_score_val)
            })

        response_data = {
            'success': True,
            'data': result,
            'pagination': {
                'total': total_count,
                'page': page,
                'limit': limit,
                'pages': (total_count + limit - 1) // limit if total_count > 0 else 1
            },
            'category': category,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"✅ Leaderboard: {len(result)} users")
        return jsonify(response_data), 200

    except ValueError as ve:
        logger.error(f"❌ Invalid parameter: {ve}")
        return jsonify({'success': False, 'error': 'Invalid pagination parameters'}), 400
    except Exception as e:
        logger.error(f"❌ Leaderboard error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch leaderboard'}), 500


@eco_score_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_eco_score_dashboard():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        trips = Trip.query.filter_by(user_id=user_id).all()

        total_distance = sum(float(t.distance_km or 0) for t in trips)
        total_co2_saved_grams = sum(float(t.co2_saved_vs_petrol_grams or 0) for t in trips)
        total_co2_saved_kg = total_co2_saved_grams / 1000 if total_co2_saved_grams else 0
        total_trees = max(1, round(total_co2_saved_kg / 20)) if total_co2_saved_kg > 0 else 0

        # Calculate eco_score from trips
        if len(trips) > 0 and total_distance > 0:
            average_eco_score = min(100, (total_co2_saved_grams / total_distance) / 100 * 100)
        else:
            average_eco_score = float(user.current_eco_score or 0)

        level = get_level_from_score(average_eco_score)
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'User'

        return jsonify({
            'success': True,
            'user': {'id': user_id, 'name': full_name, 'email': user.email, 'vehicle_model': 'Electric Vehicle'},
            'eco_score': {'score': round(average_eco_score, 2), 'level': level, 'badges': [level], 'percentile': 'N/A'},
            'statistics': {
                'total_distance': round(total_distance, 2),
                'total_trips': len(trips),
                'total_co2_saved_grams': round(total_co2_saved_grams, 0),
                'total_co2_saved_kg': round(total_co2_saved_kg, 2),
                'total_trees_equivalent': total_trees
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"❌ Dashboard error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch dashboard'}), 500


@eco_score_bp.route('/health', methods=['GET'])
def eco_score_health():
    try:
        user_count = User.query.count()
        trip_count = Trip.query.count()
        return jsonify({
            'status': 'healthy',
            'service': 'eco-score',
            'version': '1.0',
            'database': {'users': user_count, 'trips': trip_count},
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


def get_level_from_score(score):
    score = float(score or 0)
    if score >= 90: return 'Platinum'
    elif score >= 70: return 'Gold'
    elif score >= 50: return 'Silver'
    else: return 'Bronze'
