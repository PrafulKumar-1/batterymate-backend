from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
# We import all models from user.py which acts as your master model file
from app.models.user import db, User, Vehicle
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user and default vehicle"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'User already exists'}), 409
        
        # 1. Create User
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            first_name=data.get('name', '').split(' ')[0],
            last_name=' '.join(data.get('name', '').split(' ')[1:]) if ' ' in data.get('name', '') else '',
            city=data.get('city', ''),
            country=data.get('country', 'India'),
            preferred_language='en'
        )
        
        db.session.add(user)
        db.session.flush()  # FLUSH allows us to get user.id before committing
        
        # 2. Create Vehicle (CRITICAL FIX)
        vehicle_model = data.get('vehicle_model', 'Generic EV')
        vehicle = Vehicle(
            user_id=user.id,
            make='Unknown',
            model=vehicle_model,
            year=datetime.now().year,
            battery_capacity_kwh=60.0,      # Default buffer
            efficiency_kwh_per_km=0.14,     # Default efficiency
            current_battery_health=100.0,
            purchase_date=datetime.utcnow().date()
        )
        db.session.add(vehicle)
        
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # CRITICAL FIX: Cast identity to string to prevent 422 errors
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Helper to handle name splitting
        if 'name' in data:
            parts = data['name'].split(' ')
            user.first_name = parts[0]
            user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
            
        user.city = data.get('city', user.city)
        user.country = data.get('country', user.country)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500