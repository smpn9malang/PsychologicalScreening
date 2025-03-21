import os
import secrets
from datetime import timedelta

# API Configuration
API_VERSION = 'v1'
API_PREFIX = f'/api/{API_VERSION}'

# Secret key for JWT token and other security needs
SECRET_KEY = os.environ.get('API_SECRET_KEY', secrets.token_hex(32))

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# Rate Limiting
RATE_LIMIT = '100 per minute'

# CORS Configuration
CORS_ORIGINS = ['*']  # In production, this should be more restrictive

# Database Configuration
# Using the same database as the main application