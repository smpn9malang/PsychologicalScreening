import json
from datetime import datetime
from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    """Standard success response for API"""
    response = {
        'status': 'success',
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def error_response(message="An error occurred", status_code=400):
    """Standard error response for API"""
    response = {
        'status': 'error',
        'message': message
    }
    
    return jsonify(response), status_code

def parse_json_field(data, field):
    """Parse JSONB field from database"""
    if field in data and data[field]:
        if isinstance(data[field], str):
            try:
                return json.loads(data[field])
            except json.JSONDecodeError:
                return data[field]
        else:
            return data[field]
    return None

def format_datetime(dt):
    """Format datetime objects for JSON responses"""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt

def format_patient_data(patient_data):
    """Format patient data for API response"""
    if not patient_data:
        return None
    
    # Copy the data to avoid modifying the original
    formatted_data = patient_data.copy()
    
    # Format datetime fields
    if 'created_at' in formatted_data:
        formatted_data['created_at'] = format_datetime(formatted_data['created_at'])
    if 'updated_at' in formatted_data:
        formatted_data['updated_at'] = format_datetime(formatted_data['updated_at'])
    
    return formatted_data