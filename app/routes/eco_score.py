from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, EcoScore, Trip

eco_score_bp = Blueprint('eco_score', __name__, url_prefix='/api/eco-score')

@eco_score_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def eco_score_dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get recent trips for scoring
    recent_trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.completed_at.desc()).limit(10).all()
    
    avg_eco_score = sum([t.eco_score for t in recent_trips if t.eco_score]) / len([t for t in recent_trips if t.eco_score]) if recent_trips else 0
    
    # Determine badge level
    badges = []
    if avg_eco_score >= 90:
        badges = ['Planet Guardian', 'Carbon Hero']
    elif avg_eco_score >= 80:
        badges = ['Climate Champion', 'Green Driver']
    elif avg_eco_score >= 70:
        badges = ['Eco Learner', 'Tree Planter']
    
    # Calculate totals
    total_co2_saved_kg = user.total_co2_saved
    total_trees_equivalent = total_co2_saved_kg / 25  # 25 kg CO2 per tree per year
    
    return jsonify({
        'user_name': f"{user.first_name} {user.last_name}",
        'average_eco_score': round(avg_eco_score, 1),
        'rank_position': 234,  # Mock rank
        'badges': badges,
        'total_co2_saved_kg': round(total_co2_saved_kg, 2),
        'total_trees_equivalent': round(total_trees_equivalent, 2),
        'environmental_value_rupees': round(total_co2_saved_kg * 400, 2),
        'total_trips': user.total_trips,
        'monthly_improvement': 8.5,
        'community_percentage': 'Top 12%'
    }), 200

@eco_score_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def leaderboard():
    # Mock leaderboard data
    users_data = [
        {'rank': 1, 'name': 'Raj Kumar', 'eco_score': 96, 'co2_saved_kg': 450},
        {'rank': 2, 'name': 'Priya Singh', 'eco_score': 94, 'co2_saved_kg': 425},
        {'rank': 3, 'name': 'Amit Patel', 'eco_score': 89, 'co2_saved_kg': 380},
        {'rank': 4, 'name': 'You', 'eco_score': 84, 'co2_saved_kg': 320},
        {'rank': 5, 'name': 'Neha Sharma', 'eco_score': 82, 'co2_saved_kg': 310},
    ]
    
    return jsonify({
        'leaderboard': users_data,
        'your_rank': 4,
        'total_users': 1250,
        'your_percentile': 99.7
    }), 200

@eco_score_bp.route('/achievements', methods=['GET'])
@jwt_required()
def achievements():
    achievements_list = [
        {'id': 1, 'name': 'First Trip', 'description': 'Complete your first trip', 'completed': True, 'icon': '🚗'},
        {'id': 2, 'name': 'Carbon Neutral Week', 'description': 'Save 50 kg CO2 in one week', 'completed': False, 'progress': 68},
        {'id': 3, 'name': 'Tree Planter', 'description': 'Offset 1 tree worth of CO2', 'completed': True, 'icon': '🌱'},
        {'id': 4, 'name': 'Green Charger', 'description': 'Charge 10 times during renewable peak', 'completed': False, 'progress': 40},
        {'id': 5, 'name': 'Air Quality Advocate', 'description': 'Choose clean routes 20 times', 'completed': False, 'progress': 55},
    ]
    
    return jsonify(achievements_list), 200
