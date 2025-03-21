import streamlit as st
import pandas as pd
import json
from utils.db_connector import get_db_connection, test_database_connection
from utils.screening_tools import (
    get_srq20_questions,
    get_srq29_questions,
    get_dass42_questions
)

st.set_page_config(
    page_title="Screening Tools Management - PFA Counseling",
    page_icon="📋",
    layout="wide"
)

def get_all_screening_tools():
    """Get all screening tools from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM screening_tools ORDER BY name ASC")
                columns = [desc[0] for desc in cur.description]
                result = cur.fetchall()
                
                # Convert to list of dictionaries
                tools = []
                for row in result:
                    tool_dict = dict(zip(columns, row))
                    
                    # Parse JSONB fields
                    if 'questions' in tool_dict and tool_dict['questions']:
                        tool_dict['questions'] = json.loads(tool_dict['questions'])
                        
                    tools.append(tool_dict)
                
                return tools
        except Exception as e:
            st.error(f"Error retrieving screening tools: {e}")
        finally:
            conn.close()
    return []

def save_screening_tool(tool_data, tool_id=None):
    """Save or update a screening tool in the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Prepare JSON fields
                questions = json.dumps(tool_data.get('questions', []))
                
                if tool_id:  # Update existing
                    cur.execute("""
                        UPDATE screening_tools 
                        SET name = %s, description = %s, questions = %s,
                            scoring_method = %s, interpretation_guide = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        tool_data['name'],
                        tool_data['description'],
                        questions,
                        tool_data['scoring_method'],
                        tool_data['interpretation_guide'],
                        tool_id
                    ))
                else:  # Insert new
                    cur.execute("""
                        INSERT INTO screening_tools 
                        (name, description, questions, scoring_method, interpretation_guide)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        tool_data['name'],
                        tool_data['description'],
                        questions,
                        tool_data['scoring_method'],
                        tool_data['interpretation_guide']
                    ))
                
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            st.error(f"Error saving screening tool: {e}")
        finally:
            conn.close()
    return None

def delete_screening_tool(tool_id):
    """Delete a screening tool from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM screening_tools WHERE id = %s", (tool_id,))
                conn.commit()
                return True, "Screening tool deleted successfully"
        except Exception as e:
            st.error(f"Error deleting screening tool: {e}")
            return False, f"Error: {e}"
        finally:
            conn.close()
    return False, "Database connection failed"

def import_built_in_tools():
    """Import built-in screening tools to the database"""
    # SRQ-20 Tool
    srq20_data = {
        'name': 'Self-Reporting Questionnaire (SRQ-20)',
        'description': ('The SRQ-20 is a screening tool designed to identify '
                      'mental health problems, particularly anxiety and depression, '
                      'in primary care settings.'),
        'questions': [{'question': q, 'type': 'binary'} for q in get_srq20_questions()],
        'scoring_method': """
        Count the number of 'Yes' responses. 
        Score Range: 0-20
        
        Score interpretation:
        0-4: No significant mental distress
        5-7: Mild mental distress
        8-10: Moderate mental distress
        11+: Severe mental distress
        
        A score of 8 or more suggests that referral to a mental health professional should be considered.
        """,
        'interpretation_guide': """
        The SRQ-20 primarily screens for common mental disorders, focusing on anxiety and depression symptoms.
        
        It is recommended to use clinical judgment alongside the screening results, as cultural factors
        may influence responses. This tool is meant for initial screening and not for diagnosis.
        
        If suicidal ideation is endorsed (question 17), immediate assessment is recommended regardless of total score.
        """
    }
    
    # SRQ-29 Tool
    srq29_data = {
        'name': 'Self-Reporting Questionnaire (SRQ-29 WHO)',
        'description': ('The SRQ-29 WHO is an extended version of the SRQ-20 that includes '
                      'additional questions about psychotic symptoms, epileptic seizures, '
                      'and alcohol use.'),
        'questions': [{'question': q, 'type': 'binary'} for q in get_srq29_questions()],
        'scoring_method': """
        Count the number of 'Yes' responses for each subscale:
        - Anxiety/Depression (questions 1-20): Score range 0-20
        - Psychotic symptoms (questions 21-24): Score range 0-4
        - Epileptic seizures (question 25): Score range 0-1
        - Alcohol use (questions 26-29): Score range 0-4
        
        Total score range: 0-29
        
        Interpretation:
        - Anxiety/Depression: 8+ requires mental health referral
        - Psychotic symptoms: 1+ requires specialized psychiatric assessment
        - Epileptic seizures: 1 requires medical/neurological assessment
        - Alcohol use: 2+ suggests problematic alcohol use requiring specialist referral
        """,
        'interpretation_guide': """
        The SRQ-29 is more comprehensive than the SRQ-20, allowing for screening of more serious
        mental health conditions beyond anxiety and depression.
        
        Psychotic symptoms require careful assessment by a specialist. A positive response doesn't
        necessarily indicate a psychotic disorder but warrants proper evaluation.
        
        The epilepsy question is meant only for initial screening and requires proper neurological
        assessment for diagnosis.
        
        The alcohol questions are adapted from the CAGE questionnaire and help identify potential
        problematic drinking patterns.
        """
    }
    
    # DASS-42 Tool
    dass_questions = get_dass42_questions()
    formatted_questions = []
    for i, (category, question) in enumerate(dass_questions):
        formatted_questions.append({
            'question': question,
            'category': category,
            'type': 'scale',
            'options': [
                "Did not apply to me at all",
                "Applied to me to some degree",
                "Applied to me to a considerable degree",
                "Applied to me very much"
            ]
        })
    
    dass42_data = {
        'name': 'Depression Anxiety Stress Scale (DASS-42)',
        'description': ('The DASS-42 is a set of three self-report scales designed to measure '
                      'the emotional states of depression, anxiety and stress.'),
        'questions': formatted_questions,
        'scoring_method': """
        Each item is scored from 0 (did not apply) to 3 (applied very much).
        
        The assessment provides three scores:
        - Depression: Sum of scores for 14 depression items
        - Anxiety: Sum of scores for 14 anxiety items
        - Stress: Sum of scores for 14 stress items
        
        Score ranges for Depression:
        0-9: Normal
        10-13: Mild
        14-20: Moderate
        21-27: Severe
        28+: Extremely Severe
        
        Score ranges for Anxiety:
        0-7: Normal
        8-9: Mild
        10-14: Moderate
        15-19: Severe
        20+: Extremely Severe
        
        Score ranges for Stress:
        0-14: Normal
        15-18: Mild
        19-25: Moderate
        26-33: Severe
        34+: Extremely Severe
        """,
        'interpretation_guide': """
        The DASS-42 is not a diagnostic tool but provides a measure of the severity of symptoms
        related to depression, anxiety, and stress.
        
        Depression scale: Assesses dysphoria, hopelessness, devaluation of life, self-deprecation,
        lack of interest/involvement, anhedonia, and inertia.
        
        Anxiety scale: Assesses autonomic arousal, skeletal muscle effects, situational anxiety,
        and subjective experience of anxious affect.
        
        Stress scale: Assesses difficulty relaxing, nervous arousal, and being easily upset/agitated,
        irritable/over-reactive and impatient.
        
        Referral is generally recommended for scores in the moderate to extreme ranges.
        """
    }
    
    # Store tools in database
    tools = [srq20_data, srq29_data, dass42_data]
    imported_count = 0
    
    for tool in tools:
        result = save_screening_tool(tool)
        if result:
            imported_count += 1
    
    return imported_count

def main():
    st.title("Screening Tools Management")
    
    # Check database connection
    connection_status, _ = test_database_connection()
    if not connection_status:
        st.error("Database connection failed. Please check your database settings.")
        return
    
    # Sidebar for navigation
    st.sidebar.title("Actions")
    action = st.sidebar.radio("Choose an action", [
        "View Screening Tools", 
        "Add New Screening Tool", 
        "Edit Screening Tool", 
        "Delete Screening Tool",
        "Import Built-in Tools"
    ])
    
    if action == "View Screening Tools":
        st.header("Available Screening Tools")
        tools = get_all_screening_tools()
        
        if not tools:
            st.info("No screening tools found in the database. Add a new tool or import built-in tools to get started.")
        else:
            # Display as a table
            tools_table = []
            for tool in tools:
                question_count = len(tool.get('questions', [])) if isinstance(tool.get('questions', []), list) else 0
                tools_table.append({
                    "ID": tool['id'],
                    "Name": tool['name'],
                    "Questions": question_count,
                    "Last Updated": tool.get('updated_at', '')
                })
            
            df = pd.DataFrame(tools_table)
            st.dataframe(df, use_container_width=True)
            
            # Display detailed information for a selected tool
            if tools:
                tool_ids = {t['id']: t['name'] for t in tools}
                selected_id = st.selectbox("Select a tool to view details", 
                                          options=list(tool_ids.keys()),
                                          format_func=lambda x: tool_ids[x])
                
                selected_tool = next((t for t in tools if t['id'] == selected_id), None)
                
                if selected_tool:
                    st.subheader(f"Details for {selected_tool['name']}")
                    
                    with st.expander("Description", expanded=True):
                        st.write(selected_tool['description'])
                    
                    with st.expander("Questions", expanded=True):
                        questions = selected_tool.get('questions', [])
                        if isinstance(questions, list):
                            for i, q in enumerate(questions, 1):
                                if isinstance(q, dict):
                                    st.write(f"{i}. {q.get('question', '')}")
                                    if 'category' in q:
                                        st.write(f"   *Category: {q['category']}*")
                                    if 'type' in q and q['type'] == 'scale' and 'options' in q:
                                        st.write("   Options:")
                                        for j, opt in enumerate(q['options']):
                                            st.write(f"   {j}: {opt}")
                                else:
                                    st.write(f"{i}. {q}")
                        else:
                            st.write("No questions available")
                    
                    with st.expander("Scoring Method"):
                        st.write(selected_tool.get('scoring_method', 'No scoring method available'))
                    
                    with st.expander("Interpretation Guide"):
                        st.write(selected_tool.get('interpretation_guide', 'No interpretation guide available'))
    
    elif action == "Add New Screening Tool":
        st.header("Add New Screening Tool")
        
        with st.form("add_tool_form"):
            name = st.text_input("Tool Name")
            description = st.text_area("Description")
            
            # Questions - Use a simplified approach for adding questions
            st.subheader("Questions")
            st.markdown("Enter questions separated by new lines. Add *type:binary* or *type:scale* at the end of a line to specify question type.")
            questions_text = st.text_area("Questions", height=200)
            
            scoring_method = st.text_area("Scoring Method")
            interpretation_guide = st.text_area("Interpretation Guide")
            
            submitted = st.form_submit_button("Add Screening Tool")
            
            if submitted:
                if not name or not questions_text:
                    st.error("Name and questions are required fields")
                else:
                    # Parse questions
                    questions = []
                    for i, q_text in enumerate(questions_text.strip().split('\n')):
                        if q_text.strip():
                            q_parts = q_text.split('*type:')
                            question = q_parts[0].strip()
                            q_type = 'binary'  # Default
                            
                            if len(q_parts) > 1:
                                q_type = q_parts[1].strip()
                            
                            q_dict = {'question': question, 'type': q_type}
                            
                            # Add options for scale questions
                            if q_type == 'scale':
                                q_dict['options'] = [
                                    "Did not apply to me at all",
                                    "Applied to me to some degree",
                                    "Applied to me to a considerable degree",
                                    "Applied to me very much"
                                ]
                            
                            questions.append(q_dict)
                    
                    # Construct the tool data
                    tool_data = {
                        'name': name,
                        'description': description,
                        'questions': questions,
                        'scoring_method': scoring_method,
                        'interpretation_guide': interpretation_guide
                    }
                    
                    result = save_screening_tool(tool_data)
                    if result:
                        st.success(f"Screening tool '{name}' added successfully with ID: {result}")
                    else:
                        st.error("Failed to add screening tool")
    
    elif action == "Edit Screening Tool":
        st.header("Edit Screening Tool")
        
        tools = get_all_screening_tools()
        if not tools:
            st.info("No screening tools found in the database.")
            return
        
        # Select tool to edit
        tool_ids = {t['id']: t['name'] for t in tools}
        selected_id = st.selectbox("Select a tool to edit", 
                                  options=list(tool_ids.keys()),
                                  format_func=lambda x: tool_ids[x])
        
        selected_tool = next((t for t in tools if t['id'] == selected_id), None)
        
        if selected_tool:
            with st.form("edit_tool_form"):
                name = st.text_input("Tool Name", value=selected_tool['name'])
                description = st.text_area("Description", value=selected_tool['description'])
                
                # Questions - Convert existing questions back to text
                questions = selected_tool.get('questions', [])
                if isinstance(questions, list):
                    questions_text = ""
                    for q in questions:
                        if isinstance(q, dict):
                            q_text = q.get('question', '')
                            q_type = q.get('type', 'binary')
                            questions_text += f"{q_text} *type:{q_type}\n"
                        else:
                            questions_text += f"{q} *type:binary\n"
                else:
                    questions_text = ""
                
                st.subheader("Questions")
                st.markdown("Enter questions separated by new lines. Add *type:binary* or *type:scale* at the end of a line to specify question type.")
                questions_text = st.text_area("Questions", value=questions_text, height=200)
                
                scoring_method = st.text_area("Scoring Method", value=selected_tool.get('scoring_method', ''))
                interpretation_guide = st.text_area("Interpretation Guide", value=selected_tool.get('interpretation_guide', ''))
                
                submitted = st.form_submit_button("Update Screening Tool")
                
                if submitted:
                    if not name or not questions_text:
                        st.error("Name and questions are required fields")
                    else:
                        # Parse questions
                        questions = []
                        for i, q_text in enumerate(questions_text.strip().split('\n')):
                            if q_text.strip():
                                q_parts = q_text.split('*type:')
                                question = q_parts[0].strip()
                                q_type = 'binary'  # Default
                                
                                if len(q_parts) > 1:
                                    q_type = q_parts[1].strip()
                                
                                q_dict = {'question': question, 'type': q_type}
                                
                                # Add options for scale questions
                                if q_type == 'scale':
                                    q_dict['options'] = [
                                        "Did not apply to me at all",
                                        "Applied to me to some degree",
                                        "Applied to me to a considerable degree",
                                        "Applied to me very much"
                                    ]
                                
                                questions.append(q_dict)
                        
                        # Construct the tool data
                        tool_data = {
                            'name': name,
                            'description': description,
                            'questions': questions,
                            'scoring_method': scoring_method,
                            'interpretation_guide': interpretation_guide
                        }
                        
                        result = save_screening_tool(tool_data, selected_id)
                        if result:
                            st.success(f"Screening tool '{name}' updated successfully")
                        else:
                            st.error("Failed to update screening tool")
    
    elif action == "Delete Screening Tool":
        st.header("Delete Screening Tool")
        st.warning("Caution: Deleting a screening tool is permanent and cannot be undone.")
        
        tools = get_all_screening_tools()
        if not tools:
            st.info("No screening tools found in the database.")
            return
        
        # Select tool to delete
        tool_ids = {t['id']: t['name'] for t in tools}
        selected_id = st.selectbox("Select a tool to delete", 
                                  options=list(tool_ids.keys()),
                                  format_func=lambda x: tool_ids[x])
        
        selected_tool = next((t for t in tools if t['id'] == selected_id), None)
        
        if selected_tool:
            st.write(f"You are about to delete: **{selected_tool['name']}**")
            st.write(f"This tool has {len(selected_tool.get('questions', []))} questions.")
            
            # Confirmation
            if st.button("Confirm Deletion", type="primary"):
                success, message = delete_screening_tool(selected_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    elif action == "Import Built-in Tools":
        st.header("Import Built-in Screening Tools")
        st.info("""
        This action will import the following pre-configured screening tools:
        
        1. Self-Reporting Questionnaire (SRQ-20)
        2. Self-Reporting Questionnaire (SRQ-29 WHO)
        3. Depression Anxiety Stress Scale (DASS-42)
        
        If these tools already exist in the database, duplicates will be created.
        """)
        
        if st.button("Import Built-in Tools", type="primary"):
            imported_count = import_built_in_tools()
            if imported_count > 0:
                st.success(f"Successfully imported {imported_count} built-in screening tools")
            else:
                st.error("Failed to import built-in tools")

if __name__ == "__main__":
    main()