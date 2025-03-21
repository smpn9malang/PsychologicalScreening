import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field

class PsychiatristResource(Resource):
    """Resource for individual psychiatrist operations"""
    
    @token_required
    def get(self, psychiatrist_id, **kwargs):
        """Get a single psychiatrist by ID"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM psychiatrists WHERE id = %s", (psychiatrist_id,))
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Psychiatrist with ID {psychiatrist_id} not found", 404)
                    
                    psychiatrist_dict = dict(zip(columns, result))
                    
                    # Parse JSONB fields
                    if 'contact_info' in psychiatrist_dict and psychiatrist_dict['contact_info']:
                        psychiatrist_dict['contact_info'] = json.loads(psychiatrist_dict['contact_info'])
                    if 'availability' in psychiatrist_dict and psychiatrist_dict['availability']:
                        psychiatrist_dict['availability'] = json.loads(psychiatrist_dict['availability'])
                    
                    return success_response(psychiatrist_dict)
            except Exception as e:
                return error_response(f"Error retrieving psychiatrist: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def put(self, psychiatrist_id, **kwargs):
        """Update a psychiatrist"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if psychiatrist exists
                    cur.execute("SELECT * FROM psychiatrists WHERE id = %s", (psychiatrist_id,))
                    if not cur.fetchone():
                        return error_response(f"Psychiatrist with ID {psychiatrist_id} not found", 404)
                    
                    # Prepare JSON fields
                    contact_info = json.dumps(data.get('contact_info', {}))
                    availability = json.dumps(data.get('availability', {}))
                    
                    # Update the psychiatrist
                    cur.execute("""
                        UPDATE psychiatrists
                        SET name = %s, specialization = %s, qualifications = %s,
                            hospital = %s, contact_info = %s, availability = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('specialization'),
                        data.get('qualifications'),
                        data.get('hospital'),
                        contact_info,
                        availability,
                        psychiatrist_id
                    ))
                    
                    conn.commit()
                    
                    return success_response({'id': psychiatrist_id}, "Psychiatrist updated successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error updating psychiatrist: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def delete(self, psychiatrist_id, **kwargs):
        """Delete a psychiatrist"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if psychiatrist exists
                    cur.execute("SELECT * FROM psychiatrists WHERE id = %s", (psychiatrist_id,))
                    if not cur.fetchone():
                        return error_response(f"Psychiatrist with ID {psychiatrist_id} not found", 404)
                    
                    # Check if any referrals reference this psychiatrist
                    cur.execute("SELECT COUNT(*) FROM referrals WHERE psychiatrist_id = %s", (psychiatrist_id,))
                    referral_count = cur.fetchone()[0]
                    if referral_count > 0:
                        return error_response(f"Cannot delete: Psychiatrist is referenced in {referral_count} referrals", 400)
                    
                    # Delete the psychiatrist
                    cur.execute("DELETE FROM psychiatrists WHERE id = %s", (psychiatrist_id,))
                    conn.commit()
                    
                    return success_response(message=f"Psychiatrist with ID {psychiatrist_id} deleted successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error deleting psychiatrist: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class PsychiatristListResource(Resource):
    """Resource for operations on the collection of psychiatrists"""
    
    @token_required
    def get(self, **kwargs):
        """Get all psychiatrists"""
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
                    hospital = request.args.get('hospital', '')
                    
                    # Calculate offset
                    offset = (page - 1) * per_page
                    
                    # Build query based on search parameters
                    query = "SELECT * FROM psychiatrists"
                    query_params = []
                    query_conditions = []
                    
                    if search:
                        query_conditions.append("name ILIKE %s")
                        query_params.append(f"%{search}%")
                    
                    if specialization:
                        query_conditions.append("specialization ILIKE %s")
                        query_params.append(f"%{specialization}%")
                    
                    if hospital:
                        query_conditions.append("hospital ILIKE %s")
                        query_params.append(f"%{hospital}%")
                    
                    if query_conditions:
                        query += " WHERE " + " AND ".join(query_conditions)
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_psychiatrists"
                    cur.execute(count_query, query_params)
                    total_count = cur.fetchone()[0]
                    
                    # Add ordering and pagination
                    query += " ORDER BY name ASC LIMIT %s OFFSET %s"
                    query_params.extend([per_page, offset])
                    
                    # Execute final query
                    cur.execute(query, query_params)
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    psychiatrists = []
                    for row in results:
                        psychiatrist_dict = dict(zip(columns, row))
                        
                        # Parse JSONB fields
                        if 'contact_info' in psychiatrist_dict and psychiatrist_dict['contact_info']:
                            psychiatrist_dict['contact_info'] = json.loads(psychiatrist_dict['contact_info'])
                        if 'availability' in psychiatrist_dict and psychiatrist_dict['availability']:
                            psychiatrist_dict['availability'] = json.loads(psychiatrist_dict['availability'])
                        
                        psychiatrists.append(psychiatrist_dict)
                    
                    # Prepare pagination metadata
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                    
                    return success_response({
                        'psychiatrists': psychiatrists,
                        'pagination': pagination
                    })
            except Exception as e:
                return error_response(f"Error retrieving psychiatrists: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def post(self, **kwargs):
        """Create a new psychiatrist"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        # Validate required fields
        if not data.get('name') or not data.get('specialization') or not data.get('hospital'):
            return error_response("Name, specialization, and hospital are required", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Prepare JSON fields
                    contact_info = json.dumps(data.get('contact_info', {}))
                    availability = json.dumps(data.get('availability', {}))
                    
                    # Create the psychiatrist
                    cur.execute("""
                        INSERT INTO psychiatrists
                        (name, specialization, qualifications, hospital, contact_info, availability)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('specialization'),
                        data.get('qualifications', ''),
                        data.get('hospital'),
                        contact_info,
                        availability
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    return success_response({'id': result[0]}, "Psychiatrist created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating psychiatrist: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)