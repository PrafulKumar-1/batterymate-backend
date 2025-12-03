from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from datetime import datetime
import time

# Rate limiting cache
rate_limit_cache = {}

def rate_limit(max_calls=100, time_window=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            now = time.time()
            
            # Clean old entries
            if client_ip in rate_limit_cache:
                rate_limit_cache[client_ip] = [
                    t for t in rate_limit_cache[client_ip]
                    if now - t < time_window
                ]
            else:
                rate_limit_cache[client_ip] = []
            
            # Check limit
            if len(rate_limit_cache[client_ip]) >= max_calls:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Record call
            rate_limit_cache[client_ip].append(now)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def jwt_required_custom(f):
    """Custom JWT decorator with error handling"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
    return wrapped
