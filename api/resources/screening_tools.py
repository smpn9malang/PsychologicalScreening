import json
from flask import request
from flask_restful import Resource
from utils.db_connector import get_db_connection
from api.auth import token_required, admin_required
from api.utils import success_response, error_response, parse_json_field

class ScreeningToolResource(Resource):
    """Resource for individual screening tool operations"""
    
    @token_required
    def get(self, tool_id, **kwargs):
        """Get a single screening tool by ID"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM screening_tools WHERE id = %s", (tool_id,))
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Screening tool with ID {tool_id} not found", 404)
                    
                    tool_dict = dict(zip(columns, result))
                    
                    # Parse JSONB fields
                    if 'questions' in tool_dict and tool_dict['questions']:
                        tool_dict['questions'] = json.loads(tool_dict['questions'])
                    
                    return success_response(tool_dict)
            except Exception as e:
                return error_response(f"Error retrieving screening tool: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def put(self, tool_id, **kwargs):
        """Update a screening tool"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if tool exists
                    cur.execute("SELECT * FROM screening_tools WHERE id = %s", (tool_id,))
                    if not cur.fetchone():
                        return error_response(f"Screening tool with ID {tool_id} not found", 404)
                    
                    # Prepare JSON fields
                    questions = json.dumps(data.get('questions', []))
                    
                    # Update the screening tool
                    cur.execute("""
                        UPDATE screening_tools
                        SET name = %s, description = %s, questions = %s,
                            scoring_method = %s, interpretation_guide = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('description'),
                        questions,
                        data.get('scoring_method'),
                        data.get('interpretation_guide'),
                        tool_id
                    ))
                    
                    conn.commit()
                    
                    return success_response({'id': tool_id}, "Screening tool updated successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error updating screening tool: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def delete(self, tool_id, **kwargs):
        """Delete a screening tool"""
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Check if tool exists
                    cur.execute("SELECT * FROM screening_tools WHERE id = %s", (tool_id,))
                    if not cur.fetchone():
                        return error_response(f"Screening tool with ID {tool_id} not found", 404)
                    
                    # Delete the screening tool
                    cur.execute("DELETE FROM screening_tools WHERE id = %s", (tool_id,))
                    conn.commit()
                    
                    return success_response(message=f"Screening tool with ID {tool_id} deleted successfully")
            except Exception as e:
                conn.rollback()
                return error_response(f"Error deleting screening tool: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class ScreeningToolListResource(Resource):
    """Resource for operations on the collection of screening tools"""
    
    @token_required
    def get(self, **kwargs):
        """Get all screening tools"""
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
                    query = "SELECT * FROM screening_tools"
                    query_params = []
                    
                    if search:
                        query += " WHERE name ILIKE %s"
                        query_params.append(f"%{search}%")
                    
                    # Get total count
                    count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_tools"
                    cur.execute(count_query, query_params)
                    total_count = cur.fetchone()[0]
                    
                    # Add ordering and pagination
                    query += " ORDER BY name ASC LIMIT %s OFFSET %s"
                    query_params.extend([per_page, offset])
                    
                    # Execute final query
                    cur.execute(query, query_params)
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    
                    tools = []
                    for row in results:
                        tool_dict = dict(zip(columns, row))
                        
                        # Parse JSONB fields
                        if 'questions' in tool_dict and tool_dict['questions']:
                            tool_dict['questions'] = json.loads(tool_dict['questions'])
                        
                        tools.append(tool_dict)
                    
                    # Prepare pagination metadata
                    pagination = {
                        'page': page,
                        'per_page': per_page,
                        'total_count': total_count,
                        'total_pages': (total_count + per_page - 1) // per_page
                    }
                    
                    return success_response({
                        'screening_tools': tools,
                        'pagination': pagination
                    })
            except Exception as e:
                return error_response(f"Error retrieving screening tools: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)
    
    @admin_required
    def post(self, **kwargs):
        """Create a new screening tool"""
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
                    
                    # Create the screening tool
                    cur.execute("""
                        INSERT INTO screening_tools
                        (name, description, questions, scoring_method, interpretation_guide)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data.get('name'),
                        data.get('description', ''),
                        questions,
                        data.get('scoring_method', ''),
                        data.get('interpretation_guide', '')
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    return success_response({'id': result[0]}, "Screening tool created successfully", 201)
            except Exception as e:
                conn.rollback()
                return error_response(f"Error creating screening tool: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


class ScreeningResultResource(Resource):
    """Resource for screening results and scoring"""
    
    @token_required
    def post(self, **kwargs):
        """Calculate screening tool score from answers"""
        data = request.get_json()
        if not data:
            return error_response("No input data provided", 400)
        
        # Validate required fields
        if not data.get('tool_id') or not data.get('answers'):
            return error_response("Tool ID and answers are required", 400)
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Get the screening tool
                    cur.execute("SELECT * FROM screening_tools WHERE id = %s", (data.get('tool_id'),))
                    columns = [desc[0] for desc in cur.description]
                    result = cur.fetchone()
                    
                    if not result:
                        return error_response(f"Screening tool with ID {data.get('tool_id')} not found", 404)
                    
                    tool_dict = dict(zip(columns, result))
                    
                    # Parse questions
                    questions = []
                    if 'questions' in tool_dict and tool_dict['questions']:
                        questions = json.loads(tool_dict['questions'])
                    
                    # Calculate scores based on the tool type
                    tool_name = tool_dict.get('name', '').lower()
                    answers = data.get('answers', [])
                    
                    result = {
                        'tool_id': data.get('tool_id'),
                        'tool_name': tool_dict.get('name')
                    }
                    
                    # Basic scoring - count positive answers
                    total_score = sum(1 for a in answers if a)
                    result['total_score'] = total_score
                    
                    # SRQ-20 specific scoring
                    if 'srq-20' in tool_name or 'srq20' in tool_name:
                        result['interpretation'] = get_srq20_interpretation(total_score)
                    
                    # SRQ-29 specific scoring
                    elif 'srq-29' in tool_name or 'srq29' in tool_name:
                        result['subscale_scores'] = calculate_srq29_subscales(answers)
                        result['interpretations'] = get_srq29_interpretation(result['subscale_scores'])
                    
                    # DASS-42 specific scoring
                    elif 'dass' in tool_name:
                        result['subscale_scores'] = calculate_dass42_subscales(answers, questions)
                        result['interpretations'] = get_dass42_interpretation(result['subscale_scores'])
                    
                    return success_response(result)
            except Exception as e:
                return error_response(f"Error processing screening result: {str(e)}", 500)
            finally:
                conn.close()
        
        return error_response("Database connection failed", 500)


# Helper functions for screening tool scoring and interpretation

def get_srq20_interpretation(score):
    """Get interpretation for SRQ-20 score"""
    if score <= 4:
        return "No significant mental distress"
    elif score <= 7:
        return "Mild mental distress"
    elif score <= 10:
        return "Moderate mental distress"
    else:
        return "Severe mental distress"

def calculate_srq29_subscales(answers):
    """Calculate subscale scores for SRQ-29"""
    if len(answers) < 29:
        return {"error": "Insufficient answers for SRQ-29"}
    
    return {
        "anxiety_depression": sum(1 for i, a in enumerate(answers) if a and i < 20),
        "psychotic": sum(1 for i, a in enumerate(answers) if a and 20 <= i <= 23),
        "epilepsy": 1 if answers[24] else 0,
        "alcohol": sum(1 for i, a in enumerate(answers) if a and i >= 25)
    }

def get_srq29_interpretation(subscale_scores):
    """Get interpretation for SRQ-29 subscale scores"""
    interpretations = {}
    
    anxiety_depression = subscale_scores.get("anxiety_depression", 0)
    if anxiety_depression <= 4:
        interpretations["anxiety_depression"] = "No significant mental distress"
    elif anxiety_depression <= 7:
        interpretations["anxiety_depression"] = "Mild mental distress"
    elif anxiety_depression <= 10:
        interpretations["anxiety_depression"] = "Moderate mental distress"
    else:
        interpretations["anxiety_depression"] = "Severe mental distress"
    
    psychotic = subscale_scores.get("psychotic", 0)
    if psychotic == 0:
        interpretations["psychotic"] = "No psychotic symptoms indicated"
    else:
        interpretations["psychotic"] = "Psychotic symptoms indicated - requires specialist assessment"
    
    epilepsy = subscale_scores.get("epilepsy", 0)
    if epilepsy == 0:
        interpretations["epilepsy"] = "No epileptic seizures indicated"
    else:
        interpretations["epilepsy"] = "Epileptic seizures indicated - requires medical assessment"
    
    alcohol = subscale_scores.get("alcohol", 0)
    if alcohol == 0:
        interpretations["alcohol"] = "No problematic alcohol use indicated"
    elif alcohol == 1:
        interpretations["alcohol"] = "Possible problematic alcohol use"
    else:
        interpretations["alcohol"] = "Problematic alcohol use indicated - requires specialist assessment"
    
    return interpretations

def calculate_dass42_subscales(answers, questions):
    """Calculate subscale scores for DASS-42"""
    depression_score = 0
    anxiety_score = 0
    stress_score = 0
    
    # Match answers with question categories
    for i, (answer, question) in enumerate(zip(answers, questions)):
        category = question.get('category', '').lower() if isinstance(question, dict) else ''
        score = answer if isinstance(answer, int) else 0
        
        if 'depression' in category:
            depression_score += score
        elif 'anxiety' in category:
            anxiety_score += score
        elif 'stress' in category:
            stress_score += score
    
    return {
        "depression": depression_score,
        "anxiety": anxiety_score,
        "stress": stress_score
    }

def get_dass42_interpretation(subscale_scores):
    """Get interpretation for DASS-42 subscale scores"""
    interpretations = {}
    
    depression = subscale_scores.get("depression", 0)
    if depression <= 9:
        interpretations["depression"] = "Normal"
    elif depression <= 13:
        interpretations["depression"] = "Mild"
    elif depression <= 20:
        interpretations["depression"] = "Moderate"
    elif depression <= 27:
        interpretations["depression"] = "Severe"
    else:
        interpretations["depression"] = "Extremely Severe"
    
    anxiety = subscale_scores.get("anxiety", 0)
    if anxiety <= 7:
        interpretations["anxiety"] = "Normal"
    elif anxiety <= 9:
        interpretations["anxiety"] = "Mild"
    elif anxiety <= 14:
        interpretations["anxiety"] = "Moderate"
    elif anxiety <= 19:
        interpretations["anxiety"] = "Severe"
    else:
        interpretations["anxiety"] = "Extremely Severe"
    
    stress = subscale_scores.get("stress", 0)
    if stress <= 14:
        interpretations["stress"] = "Normal"
    elif stress <= 18:
        interpretations["stress"] = "Mild"
    elif stress <= 25:
        interpretations["stress"] = "Moderate"
    elif stress <= 33:
        interpretations["stress"] = "Severe"
    else:
        interpretations["stress"] = "Extremely Severe"
    
    return interpretations