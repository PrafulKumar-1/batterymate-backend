from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def token_required(f):
    """Verify JWT token is present and valid"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            return f(current_user_id, *args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Unauthorized', 'message': str(e)}), 401
    
    return decorated

def admin_required(f):
    """Verify user is admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            # Check admin status from JWT claims
            from flask_jwt_extended import get_jwt
            claims = get_jwt()
            if not claims.get('is_admin', False):
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Unauthorized'}), 401
    
    return decorated
