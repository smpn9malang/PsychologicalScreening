import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field

class ListeningTemplateResource(Resource):
    """Resource for individual listening template operations"""
    
    @token_required
    def get(self, template_id, **kwargs):
        """Get a single listening template by ID"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM listening_templates WHERE id = %s", (template_id,))
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Listening template with ID {template_id} not found", 404)
                    
                    template_dict = dict(zip(columns, result))
                    
                    # Parse JSONB fields
                    if 'questions' in template_dict and template_dict['questions']:
                        template_dict['questions'] = json.loads(template_dict['questions'])
                    
                    return success_response(template_dict)
            except Exception as e:
                return error_response(f"Error retrieving listening template: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def put(self, template_id, **kwargs):
        """Update a listening template"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if template exists
                    cur.execute("SELECT * FROM listening_templates WHERE id = %s", (template_id,))
                    if not cur.fetchone():
                        return error_response(f"Listening template with ID {template_id} not found", 404)
                    
                    # Prepare JSON fields
                    questions = json.dumps(data.get('questions', []))
                    
                    # Update the listening template
                    cur.execute("""
                        UPDATE listening_templates
                        SET name = %s, description = %s, questions = %s, guidelines = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('description'),
                        questions,
                        data.get('guidelines'),
                        template_id
                    ))
                    
                    conn.commit()
                    
                    return success_response({'id': template_id}, "Listening template updated successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error updating listening template: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def delete(self, template_id, **kwargs):
        """Delete a listening template"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if template exists
                    cur.execute("SELECT * FROM listening_templates WHERE id = %s", (template_id,))
                    if not cur.fetchone():
                        return error_response(f"Listening template with ID {template_id} not found", 404)
                    
                    # Delete the listening template
                    cur.execute("DELETE FROM listening_templates WHERE id = %s", (template_id,))
                    conn.commit()
                    
                    return success_response(message=f"Listening template with ID {template_id} deleted successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error deleting listening template: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class ListeningTemplateListResource(Resource):
    """Resource for operations on the collection of listening templates"""
    
    @token_required
    def get(self, **kwargs):
        """Get all listening templates"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Get pagination parameters
                    page = int(request.args.get('page', 1))
                    per_page = int(request.args.get('per_page', 10))
                    
                    # Get search parameter
                    search = request.args.get('search', '')
                    
                    # Calculate offset
                    offset = (page - 1) * per_page
                    
                    # Build query based on search parameters
                    query = "SELECT * FROM listening_templates"
                    query_params = []
                    
                    if search:
                        query += " WHERE name ILIKE %s"
                        query_params.append(f"%{search}%")
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_templates"
                    cur.execute(count_query, query_params)
                    total_count = cur.fetchone()[0]
                    
                    # Add ordering and pagination
                    query += " ORDER BY name ASC LIMIT %s OFFSET %s"
                    query_params.extend([per_page, offset])
                    
                    # Execute final query
                    cur.execute(query, query_params)
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    templates = []
                    for row in results:
                        template_dict = dict(zip(columns, row))
                        
                        # Parse JSONB fields
                        if 'questions' in template_dict and template_dict['questions']:
                            template_dict['questions'] = json.loads(template_dict['questions'])
                        
                        templates.append(template_dict)
                    
                    # Prepare pagination metadata
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                    
                    return success_response({
                        'listening_templates': templates,
                        'pagination': pagination
                    })
            except Exception as e:
                return error_response(f"Error retrieving listening templates: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def post(self, **kwargs):
        """Create a new listening template"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        # Validate required fields
        if not data.get('name') or not data.get('questions'):
            return error_response("Name and questions are required", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Prepare JSON fields
                    questions = json.dumps(data.get('questions', []))
                    
                    # Create the listening template
                    cur.execute("""
                        INSERT INTO listening_templates
                        (name, description, questions, guidelines)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('description', ''),
                        questions,
                        data.get('guidelines', '')
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    return success_response({'id': result[0]}, "Listening template created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating listening template: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)