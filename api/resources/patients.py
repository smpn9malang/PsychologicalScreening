import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field, format_patient_data, format_datetime

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
                    # Check if patient exists
                    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                    if not cur.fetchone():
                        return error_response(f"Patient with ID {patient_id} not found", 404)
                    
                    # Prepare JSON fields
                    personal_data = json.dumps(data.get('personal_data', {}))
                    assessment_data = json.dumps(data.get('assessment_data', {}))
                    listening_data = json.dumps(data.get('listening_data', {}))
                    screening_data = json.dumps(data.get('screening_data', {}))
                    
                    # Update the patient
                    cur.execute("""
                        UPDATE patients
                        SET name = %s, age = %s, gender = %s,
                            personal_data = %s, assessment_data = %s,
                            listening_data = %s, screening_data = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('age'),
                        data.get('gender'),
                        personal_data,
                        assessment_data,
                        listening_data,
                        screening_data,
                        patient_id
                    ))
                    
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
                    
                    # Check if any referrals reference this patient
                    cur.execute("SELECT COUNT(*) FROM referrals WHERE patient_id = %s", (patient_id,))
                    referral_count = cur.fetchone()[0]
                    if referral_count > 0:
                        return error_response(f"Cannot delete: Patient is referenced in {referral_count} referrals", 400)
                    
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
                    
                    # Get search parameter
                    search = request.args.get('search', '')
                    gender = request.args.get('gender', '')
                    min_age = request.args.get('min_age')
                    max_age = request.args.get('max_age')
                    
                    # Calculate offset
                    offset = (page - 1) * per_page
                    
                    # Build query based on search parameters
                    query = "SELECT * FROM patients"
                    query_params = []
                    query_conditions = []
                    
                    if search:
                        query_conditions.append("name ILIKE %s")
                        query_params.append(f"%{search}%")
                    
                    if gender:
                        query_conditions.append("gender = %s")
                        query_params.append(gender)
                    
                    if min_age:
                        query_conditions.append("age >= %s")
                        query_params.append(int(min_age))
                    
                    if max_age:
                        query_conditions.append("age <= %s")
                        query_params.append(int(max_age))
                    
                    if query_conditions:
                        query += " WHERE " + " AND ".join(query_conditions)
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_patients"
                    cur.execute(count_query, query_params)
                    total_count = cur.fetchone()[0]
                    
                    # Add ordering and pagination
                    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                    query_params.extend([per_page, offset])
                    
                    # Execute final query
                    cur.execute(query, query_params)
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    patients = []
                    for row in results:
                        patient_dict = dict(zip(columns, row))
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
        
        # Validate required fields
        if not data.get('name'):
            return error_response("Patient name is required", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Prepare JSON fields
                    personal_data = json.dumps(data.get('personal_data', {}))
                    assessment_data = json.dumps(data.get('assessment_data', {}))
                    listening_data = json.dumps(data.get('listening_data', {}))
                    screening_data = json.dumps(data.get('screening_data', {}))
                    
                    # Create the patient
                    cur.execute("""
                        INSERT INTO patients
                        (name, age, gender, personal_data, assessment_data, listening_data, screening_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('age'),
                        data.get('gender', ''),
                        personal_data,
                        assessment_data,
                        listening_data,
                        screening_data
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    return success_response({'id': result[0]}, "Patient created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating patient: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)