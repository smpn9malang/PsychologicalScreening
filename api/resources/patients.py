import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field, format_patient_data

class PatientResource(Resource):
    """Resource for individual patient operations"""
    
    @token_required
    def get(self, patient_id, **kwargs):
        """Get a single patient by ID"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Patient with ID {patient_id} not found", 404)
                    
                    patient_dict = dict(zip(columns, result))
                    
                    # Parse the JSONB data field
                    if 'data' in patient_dict and patient_dict['data']:
                        patient_dict['data'] = json.loads(patient_dict['data'])
                    
                    # Format data for API response
                    formatted_patient = format_patient_data(patient_dict)
                    
                    return success_response(formatted_patient)
            except Exception as e:
                return error_response(f"Error retrieving patient: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @token_required
    def put(self, patient_id, **kwargs):
        """Update a patient"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # First check if patient exists
                    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                    if not cur.fetchone():
                        return error_response(f"Patient with ID {patient_id} not found", 404)
                    
                    # Retrieve existing data
                    cur.execute("SELECT data FROM patients WHERE id = %s", (patient_id,))
                    result = cur.fetchone()
                    existing_data = json.loads(result[0]) if result else {}
                    
                    # Merge existing data with new data
                    existing_data.update(data)
                    updated_data = json.dumps(existing_data)
                    
                    # Update the patient
                    cur.execute("""
                        UPDATE patients 
                        SET data = %s
                        WHERE id = %s
                        RETURNING id
                    """, (updated_data, patient_id))
                    
                    conn.commit()
                    
                    return success_response({'id': patient_id}, "Patient updated successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error updating patient: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def delete(self, patient_id, **kwargs):
        """Delete a patient"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if patient exists
                    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                    if not cur.fetchone():
                        return error_response(f"Patient with ID {patient_id} not found", 404)
                    
                    # Check if patient has associated referrals
                    cur.execute("SELECT COUNT(*) FROM referrals WHERE patient_id = %s", (patient_id,))
                    referral_count = cur.fetchone()[0]
                    
                    if referral_count > 0:
                        # Delete associated referrals first
                        cur.execute("DELETE FROM referrals WHERE patient_id = %s", (patient_id,))
                    
                    # Delete the patient
                    cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
                    conn.commit()
                    
                    return success_response(message=f"Patient with ID {patient_id} deleted successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error deleting patient: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class PatientListResource(Resource):
    """Resource for operations on the collection of patients"""
    
    @token_required
    def get(self, **kwargs):
        """Get all patients"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Get pagination parameters
                    page = int(request.args.get('page', 1))
                    per_page = int(request.args.get('per_page', 10))
                    
                    # Calculate offset
                    offset = (page - 1) * per_page
                    
                    # Get total count
                    cur.execute("SELECT COUNT(*) FROM patients")
                    total_count = cur.fetchone()[0]
                    
                    # Get paginated results
                    cur.execute("""
                        SELECT * FROM patients 
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (per_page, offset))
                    
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    patients = []
                    for row in results:
                        patient_dict = dict(zip(columns, row))
                        
                        # Parse the JSONB data field
                        if 'data' in patient_dict and patient_dict['data']:
                            patient_dict['data'] = json.loads(patient_dict['data'])
                        
                        # Format data for API response
                        formatted_patient = format_patient_data(patient_dict)
                        patients.append(formatted_patient)
                    
                    # Prepare pagination metadata
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                    
                    return success_response({
                        'patients': patients,
                        'pagination': pagination
                    })
            except Exception as e:
                return error_response(f"Error retrieving patients: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @token_required
    def post(self, **kwargs):
        """Create a new patient"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        if 'id' not in data:
            return error_response("Patient ID is required", 400)
        
        patient_id = data.pop('id')
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if patient already exists
                    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                    if cur.fetchone():
                        return error_response(f"Patient with ID {patient_id} already exists", 409)
                    
                    # Create the patient
                    patient_data = json.dumps(data)
                    cur.execute("""
                        INSERT INTO patients (id, data)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (patient_id, patient_data))
                    
                    conn.commit()
                    
                    return success_response({'id': patient_id}, "Patient created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating patient: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)