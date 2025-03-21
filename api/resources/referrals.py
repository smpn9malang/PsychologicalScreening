import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field, format_datetime

class ReferralResource(Resource):
    """Resource for individual referral operations"""
    
    @token_required
    def get(self, referral_id, **kwargs):
        """Get a single referral by ID"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT r.*, 
                               c.name as consultant_name,
                               p.name as psychiatrist_name
                        FROM referrals r
                        LEFT JOIN consultants c ON r.consultant_id = c.id
                        LEFT JOIN psychiatrists p ON r.psychiatrist_id = p.id
                        WHERE r.id = %s
                    """, (referral_id,))
                    
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Referral with ID {referral_id} not found", 404)
                    
                    referral_dict = dict(zip(columns, result))
                    
                    # Format datetime fields
                    if 'created_at' in referral_dict:
                        referral_dict['created_at'] = format_datetime(referral_dict['created_at'])
                    if 'updated_at' in referral_dict:
                        referral_dict['updated_at'] = format_datetime(referral_dict['updated_at'])
                    if 'appointment_date' in referral_dict and referral_dict['appointment_date']:
                        referral_dict['appointment_date'] = format_datetime(referral_dict['appointment_date'])
                    
                    return success_response(referral_dict)
            except Exception as e:
                return error_response(f"Error retrieving referral: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @token_required
    def put(self, referral_id, **kwargs):
        """Update a referral"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if referral exists
                    cur.execute("SELECT * FROM referrals WHERE id = %s", (referral_id,))
                    if not cur.fetchone():
                        return error_response(f"Referral with ID {referral_id} not found", 404)
                    
                    # Update the referral
                    cur.execute("""
                        UPDATE referrals
                        SET patient_id = %s,
                            consultant_id = %s,
                            psychiatrist_id = %s,
                            reason = %s,
                            notes = %s,
                            status = %s,
                            appointment_date = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        data.get('patient_id'),
                        data.get('consultant_id'),
                        data.get('psychiatrist_id'),
                        data.get('reason'),
                        data.get('notes'),
                        data.get('status'),
                        data.get('appointment_date'),
                        referral_id
                    ))
                    
                    conn.commit()
                    
                    return success_response({'id': referral_id}, "Referral updated successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error updating referral: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def delete(self, referral_id, **kwargs):
        """Delete a referral"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if referral exists
                    cur.execute("SELECT * FROM referrals WHERE id = %s", (referral_id,))
                    if not cur.fetchone():
                        return error_response(f"Referral with ID {referral_id} not found", 404)
                    
                    # Delete the referral
                    cur.execute("DELETE FROM referrals WHERE id = %s", (referral_id,))
                    conn.commit()
                    
                    return success_response(message=f"Referral with ID {referral_id} deleted successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error deleting referral: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class ReferralListResource(Resource):
    """Resource for operations on the collection of referrals"""
    
    @token_required
    def get(self, **kwargs):
        """Get all referrals with filtering options"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Get pagination parameters
                    page = int(request.args.get('page', 1))
                    per_page = int(request.args.get('per_page', 10))
                    
                    # Get filter parameters
                    patient_id = request.args.get('patient_id')
                    consultant_id = request.args.get('consultant_id')
                    psychiatrist_id = request.args.get('psychiatrist_id')
                    status = request.args.get('status')
                    
                    # Calculate offset
                    offset = (page - 1) * per_page
                    
                    # Build query based on filter parameters
                    query = """
                        SELECT r.*, 
                               c.name as consultant_name,
                               p.name as psychiatrist_name
                        FROM referrals r
                        LEFT JOIN consultants c ON r.consultant_id = c.id
                        LEFT JOIN psychiatrists p ON r.psychiatrist_id = p.id
                    """
                    query_params = []
                    query_conditions = []
                    
                    if patient_id:
                        query_conditions.append("r.patient_id = %s")
                        query_params.append(patient_id)
                    
                    if consultant_id:
                        query_conditions.append("r.consultant_id = %s")
                        query_params.append(consultant_id)
                    
                    if psychiatrist_id:
                        query_conditions.append("r.psychiatrist_id = %s")
                        query_params.append(psychiatrist_id)
                    
                    if status:
                        query_conditions.append("r.status = %s")
                        query_params.append(status)
                    
                    if query_conditions:
                        query += " WHERE " + " AND ".join(query_conditions)
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_referrals"
                    cur.execute(count_query, query_params)
                    total_count = cur.fetchone()[0]
                    
                    # Add ordering and pagination
                    query += " ORDER BY r.created_at DESC LIMIT %s OFFSET %s"
                    query_params.extend([per_page, offset])
                    
                    # Execute final query
                    cur.execute(query, query_params)
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    referrals = []
                    for row in results:
                        referral_dict = dict(zip(columns, row))
                        
                        # Format datetime fields
                        if 'created_at' in referral_dict:
                            referral_dict['created_at'] = format_datetime(referral_dict['created_at'])
                        if 'updated_at' in referral_dict:
                            referral_dict['updated_at'] = format_datetime(referral_dict['updated_at'])
                        if 'appointment_date' in referral_dict and referral_dict['appointment_date']:
                            referral_dict['appointment_date'] = format_datetime(referral_dict['appointment_date'])
                        
                        referrals.append(referral_dict)
                    
                    # Prepare pagination metadata
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                    
                    return success_response({
                        'referrals': referrals,
                        'pagination': pagination
                    })
            except Exception as e:
                return error_response(f"Error retrieving referrals: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @token_required
    def post(self, **kwargs):
        """Create a new referral"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        # Validate required fields
        if not data.get('patient_id') or not data.get('reason'):
            return error_response("Patient ID and reason are required", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if patient exists
                    cur.execute("SELECT * FROM patients WHERE id = %s", (data.get('patient_id'),))
                    if not cur.fetchone():
                        return error_response(f"Patient with ID {data.get('patient_id')} not found", 404)
                    
                    # Verify consultant if provided
                    if data.get('consultant_id'):
                        cur.execute("SELECT * FROM consultants WHERE id = %s", (data.get('consultant_id'),))
                        if not cur.fetchone():
                            return error_response(f"Consultant with ID {data.get('consultant_id')} not found", 404)
                    
                    # Verify psychiatrist if provided
                    if data.get('psychiatrist_id'):
                        cur.execute("SELECT * FROM psychiatrists WHERE id = %s", (data.get('psychiatrist_id'),))
                        if not cur.fetchone():
                            return error_response(f"Psychiatrist with ID {data.get('psychiatrist_id')} not found", 404)
                    
                    # Create the referral
                    cur.execute("""
                        INSERT INTO referrals
                        (patient_id, consultant_id, psychiatrist_id, reason, notes, status, appointment_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data.get('patient_id'),
                        data.get('consultant_id'),
                        data.get('psychiatrist_id'),
                        data.get('reason'),
                        data.get('notes', ''),
                        data.get('status', 'pending'),
                        data.get('appointment_date')
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    return success_response({'id': result[0]}, "Referral created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating referral: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class PatientReferralsResource(Resource):
    """Resource for getting all referrals for a specific patient"""
    
    @token_required
    def get(self, patient_id, **kwargs):
        """Get all referrals for a patient"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if patient exists
                    cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                    if not cur.fetchone():
                        return error_response(f"Patient with ID {patient_id} not found", 404)
                    
                    # Get all referrals for this patient
                    cur.execute("""
                        SELECT r.*, 
                               c.name as consultant_name,
                               p.name as psychiatrist_name
                        FROM referrals r
                        LEFT JOIN consultants c ON r.consultant_id = c.id
                        LEFT JOIN psychiatrists p ON r.psychiatrist_id = p.id
                        WHERE r.patient_id = %s
                        ORDER BY r.created_at DESC
                    """, (patient_id,))
                    
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    referrals = []
                    for row in results:
                        referral_dict = dict(zip(columns, row))
                        
                        # Format datetime fields
                        if 'created_at' in referral_dict:
                            referral_dict['created_at'] = format_datetime(referral_dict['created_at'])
                        if 'updated_at' in referral_dict:
                            referral_dict['updated_at'] = format_datetime(referral_dict['updated_at'])
                        if 'appointment_date' in referral_dict and referral_dict['appointment_date']:
                            referral_dict['appointment_date'] = format_datetime(referral_dict['appointment_date'])
                        
                        referrals.append(referral_dict)
                    
                    return success_response({'referrals': referrals})
            except Exception as e:
                return error_response(f"Error retrieving patient referrals: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)