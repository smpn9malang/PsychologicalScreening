import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from api.config import SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES

def generate_token(user_id, additional_claims=None):
    """Generate a JWT token for a user"""
    payload = {
        'exp': datetime.datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm='HS256'
    )

def token_required(f):
    """Decorator for routes that require a valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!', 'status': 'error'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!', 'status': 'error'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!', 'status': 'error'}), 401
        
        # Add current user info to kwargs
        kwargs['current_user_id'] = current_user_id
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator for routes that require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!', 'status': 'error'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['sub']
            
            # Check if user is admin
            if not data.get('is_admin', False):
                return jsonify({'message': 'Admin privileges required!', 'status': 'error'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!', 'status': 'error'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!', 'status': 'error'}), 401
        
        # Add current user info to kwargs
        kwargs['current_user_id'] = current_user_id
        
        return f(*args, **kwargs)
    
    return decorated