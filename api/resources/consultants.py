import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field

class ConsultantResource(Resource):
    """Resource for individual consultant operations"""
    
    @token_required
    def get(self, consultant_id, **kwargs):
        """Get a single consultant by ID"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM consultants WHERE id = %s", (consultant_id,))
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Consultant with ID {consultant_id} not found", 404)
                    
                    consultant_dict = dict(zip(columns, result))
                    
                    # Parse JSONB fields
                    if 'contact_info' in consultant_dict and consultant_dict['contact_info']:
                        consultant_dict['contact_info'] = json.loads(consultant_dict['contact_info'])
                    if 'availability' in consultant_dict and consultant_dict['availability']:
                        consultant_dict['availability'] = json.loads(consultant_dict['availability'])
                    
                    return success_response(consultant_dict)
            except Exception as e:
                return error_response(f"Error retrieving consultant: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def put(self, consultant_id, **kwargs):
        """Update a consultant"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if consultant exists
                    cur.execute("SELECT * FROM consultants WHERE id = %s", (consultant_id,))
                    if not cur.fetchone():
                        return error_response(f"Consultant with ID {consultant_id} not found", 404)
                    
                    # Prepare JSON fields
                    contact_info = json.dumps(data.get('contact_info', {}))
                    availability = json.dumps(data.get('availability', {}))
                    
                    # Update the consultant
                    cur.execute("""
                        UPDATE consultants
                        SET name = %s, specialization = %s, qualifications = %s,
                            contact_info = %s, availability = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('specialization'),
                        data.get('qualifications'),
                        contact_info,
                        availability,
                        consultant_id
                    ))
                    
                    conn.commit()
                    
                    return success_response({'id': consultant_id}, "Consultant updated successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error updating consultant: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def delete(self, consultant_id, **kwargs):
        """Delete a consultant"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if consultant exists
                    cur.execute("SELECT * FROM consultants WHERE id = %s", (consultant_id,))
                    if not cur.fetchone():
                        return error_response(f"Consultant with ID {consultant_id} not found", 404)
                    
                    # Check if any referrals reference this consultant
                    cur.execute("SELECT COUNT(*) FROM referrals WHERE consultant_id = %s", (consultant_id,))
                    referral_count = cur.fetchone()[0]
                    if referral_count > 0:
                        return error_response(f"Cannot delete: Consultant is referenced in {referral_count} referrals", 400)
                    
                    # Delete the consultant
                    cur.execute("DELETE FROM consultants WHERE id = %s", (consultant_id,))
                    conn.commit()
                    
                    return success_response(message=f"Consultant with ID {consultant_id} deleted successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error deleting consultant: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class ConsultantListResource(Resource):
    """Resource for operations on the collection of consultants"""
    
    @token_required
    def get(self, **kwargs):
        """Get all consultants"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Get pagination parameters
                    page = int(request.args.get('page', 1))
                    per_page = int(request.args.get('per_page', 10))
                    
                    # Get search parameter
                    search = request.args.get('search', '')
                    specialization = request.args.get('specialization', '')
                    
                    # Calculate offset
                    offset = (page - 1) * per_page
                    
                    # Build query based on search parameters
                    query = "SELECT * FROM consultants"
                    query_params = []
                    query_conditions = []
                    
                    if search:
                        query_conditions.append("name ILIKE %s")
                        query_params.append(f"%{search}%")
                    
                    if specialization:
                        query_conditions.append("specialization ILIKE %s")
                        query_params.append(f"%{specialization}%")
                    
                    if query_conditions:
                        query += " WHERE " + " AND ".join(query_conditions)
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_consultants"
                    cur.execute(count_query, query_params)
                    total_count = cur.fetchone()[0]
                    
                    # Add ordering and pagination
                    query += " ORDER BY name ASC LIMIT %s OFFSET %s"
                    query_params.extend([per_page, offset])
                    
                    # Execute final query
                    cur.execute(query, query_params)
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    consultants = []
                    for row in results:
                        consultant_dict = dict(zip(columns, row))
                        
                        # Parse JSONB fields
                        if 'contact_info' in consultant_dict and consultant_dict['contact_info']:
                            consultant_dict['contact_info'] = json.loads(consultant_dict['contact_info'])
                        if 'availability' in consultant_dict and consultant_dict['availability']:
                            consultant_dict['availability'] = json.loads(consultant_dict['availability'])
                        
                        consultants.append(consultant_dict)
                    
                    # Prepare pagination metadata
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                    
                    return success_response({
                        'consultants': consultants,
                        'pagination': pagination
                    })
            except Exception as e:
                return error_response(f"Error retrieving consultants: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def post(self, **kwargs):
        """Create a new consultant"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        # Validate required fields
        if not data.get('name') or not data.get('specialization'):
            return error_response("Name and specialization are required", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Prepare JSON fields
                    contact_info = json.dumps(data.get('contact_info', {}))
                    availability = json.dumps(data.get('availability', {}))
                    
                    # Create the consultant
                    cur.execute("""
                        INSERT INTO consultants
                        (name, specialization, qualifications, contact_info, availability)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('specialization'),
                        data.get('qualifications', ''),
                        contact_info,
                        availability
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    return success_response({'id': result[0]}, "Consultant created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating consultant: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)