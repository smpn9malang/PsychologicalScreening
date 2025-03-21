import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import generate_token
from api.utils import success_response, error_response

class LoginResource(Resource):
    """Resource for user authentication"""
    
    def post(self):
        """Login endpoint to get authentication token"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        # Get username and password
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return error_response("Username and password are required", 400)
        
        # For demonstration purposes, we'll use hard-coded credentials
        # In production, this should be replaced with proper user authentication
        if username == "admin" and password == "admin":
            # Generate a token with admin privileges
            token = generate_token("admin", {"is_admin": True})
            return success_response({
                'token': token,
                'user': {
                    'id': 'admin',
                    'username': 'admin',
                    'is_admin': True
                }
            })
        elif username == "user" and password == "user":
            # Generate a token for regular user
            token = generate_token("user", {"is_admin": False})
            return success_response({
                'token': token,
                'user': {
                    'id': 'user',
                    'username': 'user',
                    'is_admin': False
                }
            })
        else:
            return error_response("Invalid username or password", 401)


class VerifyTokenResource(Resource):
    """Resource for verifying JWT token"""
    
    def post(self):
        """Verify that a token is valid"""
        data = request.get_json()
        if not data or 'token' not in data:
            return error_response("Token is required", 400)
        
        # The token_required decorator will handle token verification
        # If the request reaches here, the token is valid
        token = data.get('token')
        
        # This is just a placeholder - the actual validation is done in the auth.py middleware
        # We would need to decode the token and check its validity
        try:
            import jwt
            from api.config import SECRET_KEY
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return success_response({
                'valid': True,
                'user_id': payload.get('sub'),
                'is_admin': payload.get('is_admin', False)
            })
        except jwt.ExpiredSignatureError:
            return error_response("Token has expired", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid token", 401)
        except Exception as e:
            return error_response(f"Error verifying token: {str(e)}", 500)