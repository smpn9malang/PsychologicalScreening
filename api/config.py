# Configuration for the API

# JWT Secret Key
SECRET_KEY = "your-secret-key-here"  # This should be changed in production

# API Versioning
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Request Rate Limiting
RATE_LIMIT_DEFAULT = "100 per day, 10 per minute"
RATE_LIMIT_AUTH_ENDPOINTS = "20 per day, 5 per minute"

# CORS Settings
CORS_ORIGINS = ["*"]  # In production, this should be restricted to specific origins

# Default pagination settings
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100