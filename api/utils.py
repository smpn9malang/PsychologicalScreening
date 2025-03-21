import json
import datetime
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
        try:
            if isinstance(data[field], str):
                return json.loads(data[field])
            return data[field]
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

def format_datetime(dt):
    """Format datetime objects for JSON responses"""
    if dt is None:
        return None
    
    if isinstance(dt, datetime.datetime):
        return dt.isoformat()
    elif isinstance(dt, datetime.date):
        return dt.isoformat()
    
    return dt  # Return as-is if not a datetime object

def format_patient_data(patient_data):
    """Format patient data for API response"""
    if not patient_data:
        return None
    
    # Format datetime fields
    if 'created_at' in patient_data:
        patient_data['created_at'] = format_datetime(patient_data['created_at'])
    if 'updated_at' in patient_data:
        patient_data['updated_at'] = format_datetime(patient_data['updated_at'])
    
    # Parse JSONB fields
    for field in ['personal_data', 'assessment_data', 'listening_data', 'screening_data']:
        if field in patient_data and patient_data[field]:
            try:
                if isinstance(patient_data[field], str):
                    patient_data[field] = json.loads(patient_data[field])
            except (json.JSONDecodeError, TypeError):
                patient_data[field] = {}
    
    return patient_data