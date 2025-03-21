import jwt
import datetime
from functools import wraps
from flask import request, g
from api.utils import error_response
from api.config import SECRET_KEY

def generate_token(user_id, additional_claims=None):
    """Generate a JWT token for a user"""
    # Set token expiration to 24 hours
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    
    # Create the JWT payload
    payload = {
        'sub': user_id,
        'exp': expiration
    }
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Generate the token
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    return token

def token_required(f):
    """Decorator for routes that require a valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return error_response("Authentication token is missing", 401)
        
        try:
            # Decode the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            g.user_id = payload['sub']
            g.is_admin = payload.get('is_admin', False)
            
            # Add user details to kwargs
            kwargs['user_id'] = g.user_id
            kwargs['is_admin'] = g.is_admin
            
        except jwt.ExpiredSignatureError:
            return error_response("Authentication token has expired", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid authentication token", 401)
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator for routes that require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # First verify that a valid token is provided
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return error_response("Authentication token is missing", 401)
        
        try:
            # Decode the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            g.user_id = payload['sub']
            g.is_admin = payload.get('is_admin', False)
            
            # Add user details to kwargs
            kwargs['user_id'] = g.user_id
            kwargs['is_admin'] = g.is_admin
            
            # Check if user has admin privileges
            if not g.is_admin:
                return error_response("Admin privileges required", 403)
            
        except jwt.ExpiredSignatureError:
            return error_response("Authentication token has expired", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid authentication token", 401)
        
        return f(*args, **kwargs)
    
    return decorated