import streamlit as st
import pandas as pd
import json
from utils.db_connector import get_db_connection, test_database_connection

st.set_page_config(
    page_title="Listening Module Management - PFA Counseling",
    page_icon="👂",
    layout="wide"
)

def get_all_listening_templates():
    """Get all listening templates from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM listening_templates ORDER BY name ASC")
                columns = [desc[0] for desc in cur.description]
                result = cur.fetchall()
                
                # Convert to list of dictionaries
                templates = []
                for row in result:
                    template_dict = dict(zip(columns, row))
                    
                    # Parse JSONB fields
                    if 'questions' in template_dict and template_dict['questions']:
                        template_dict['questions'] = json.loads(template_dict['questions'])
                        
                    templates.append(template_dict)
                
                return templates
        except Exception as e:
            st.error(f"Error retrieving listening templates: {e}")
        finally:
            conn.close()
    return []

def save_listening_template(template_data, template_id=None):
    """Save or update a listening template in the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Prepare JSON fields
                questions = json.dumps(template_data.get('questions', []))
                
                if template_id:  # Update existing
                    cur.execute("""
                        UPDATE listening_templates 
                        SET name = %s, description = %s, questions = %s, guidelines = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        template_data['name'],
                        template_data['description'],
                        questions,
                        template_data['guidelines'],
                        template_id
                    ))
                else:  # Insert new
                    cur.execute("""
                        INSERT INTO listening_templates 
                        (name, description, questions, guidelines)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        template_data['name'],
                        template_data['description'],
                        questions,
                        template_data['guidelines']
                    ))
                
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            st.error(f"Error saving listening template: {e}")
        finally:
            conn.close()
    return None

def delete_listening_template(template_id):
    """Delete a listening template from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM listening_templates WHERE id = %s", (template_id,))
                conn.commit()
                return True, "Listening template deleted successfully"
        except Exception as e:
            st.error(f"Error deleting listening template: {e}")
            return False, f"Error: {e}"
        finally:
            conn.close()
    return False, "Database connection failed"

def import_default_templates():
    """Import default listening templates to the database"""
    # Standard PFA Listening Template
    pfa_listening = {
        'name': 'Standard PFA Listening Session',
        'description': 'A structured approach to psychological first aid listening sessions based on WHO guidelines.',
        'questions': [
            {
                'category': 'Presenting Problems',
                'question': 'What brings you here today?',
                'type': 'text',
                'required': True
            },
            {
                'category': 'Presenting Problems',
                'question': 'When did you first notice these concerns?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Narrative',
                'question': 'Can you tell me more about your experience?',
                'type': 'textarea',
                'required': True
            },
            {
                'category': 'Emotional State',
                'question': 'What emotions are you experiencing now?',
                'type': 'select',
                'options': [
                    'Sadness', 'Anxiety', 'Fear', 'Anger', 'Helplessness', 
                    'Hopelessness', 'Guilt', 'Shame', 'Numbness', 'Other'
                ],
                'required': True
            },
            {
                'category': 'Emotional State',
                'question': 'How intense are these emotions (1-10 scale)?',
                'type': 'slider',
                'min': 1,
                'max': 10,
                'required': True
            },
            {
                'category': 'Support Systems',
                'question': 'Who do you have for support in your life?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Coping Strategies',
                'question': 'What has helped you cope with difficulties in the past?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Risk Assessment',
                'question': 'Have you had thoughts about harming yourself?',
                'type': 'select',
                'options': [
                    'No suicidal thoughts', 
                    'Passive ideation', 
                    'Active ideation without plan', 
                    'Active ideation with plan', 
                    'Recent attempt'
                ],
                'required': True
            },
            {
                'category': 'Risk Assessment',
                'question': 'Have you had thoughts about harming others?',
                'type': 'select',
                'options': ['None', 'Low', 'Moderate', 'High'],
                'required': True
            }
        ],
        'guidelines': """
        # Listening Session Guidelines
        
        ## Principles of PFA Listening
        
        1. **Create a safe space** - Find a quiet, private location for the conversation
        2. **Be present and attentive** - Give your full attention to the person
        3. **Use active listening** - Reflect back what you hear, ask clarifying questions
        4. **Avoid judgment** - Be accepting and non-judgmental
        5. **Respect confidentiality** - Ensure privacy except when safety is at risk
        
        ## Key Techniques
        
        - Maintain appropriate eye contact
        - Use open body language
        - Allow silences
        - Validate feelings and experiences
        - Use open-ended questions
        - Avoid giving advice or false reassurance
        - Watch for signs of distress during the conversation
        
        ## Risk Assessment
        
        If the person indicates thoughts of suicide or harm to others:
        
        - Ask direct questions about plans and intentions
        - Assess if they have means to carry out the plan
        - Determine if there is imminent danger
        - Contact emergency services if necessary
        - Never leave a high-risk individual alone
        
        ## Closing the Session
        
        - Summarize key points from the conversation
        - Identify next steps and resources
        - Schedule follow-up if appropriate
        - Provide emergency contact information
        """
    }
    
    # Youth-focused Listening Template
    youth_listening = {
        'name': 'Youth-Focused Listening Session',
        'description': 'A tailored approach for conducting psychological first aid listening sessions with adolescents and young adults.',
        'questions': [
            {
                'category': 'Presenting Problems',
                'question': 'What\'s been going on that brought you here today?',
                'type': 'text',
                'required': True
            },
            {
                'category': 'School/Work',
                'question': 'How have things been going at school/work?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Relationships',
                'question': 'How are things with your friends and family?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Narrative',
                'question': 'Can you tell me more about what\'s been happening?',
                'type': 'textarea',
                'required': True
            },
            {
                'category': 'Emotional State',
                'question': 'What feelings have you been having lately?',
                'type': 'select',
                'options': [
                    'Sadness', 'Worry', 'Fear', 'Anger', 'Overwhelmed', 
                    'Hopelessness', 'Embarrassment', 'Loneliness', 'Numbness', 'Other'
                ],
                'required': True
            },
            {
                'category': 'Emotional State',
                'question': 'On a scale of 1-10, how strong are these feelings?',
                'type': 'slider',
                'min': 1,
                'max': 10,
                'required': True
            },
            {
                'category': 'Support Systems',
                'question': 'Who do you talk to when you\'re having a hard time?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Coping Strategies',
                'question': 'What do you do to feel better when you\'re upset?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Online/Social Media',
                'question': 'How do you use social media or online platforms?',
                'type': 'text',
                'required': False
            },
            {
                'category': 'Risk Assessment',
                'question': 'Have you had thoughts about hurting yourself?',
                'type': 'select',
                'options': [
                    'No thoughts of self-harm', 
                    'Occasional thoughts without plan', 
                    'Frequent thoughts without plan', 
                    'Thoughts with plan', 
                    'Recent self-harm'
                ],
                'required': True
            },
            {
                'category': 'Risk Assessment',
                'question': 'Have you had thoughts about hurting others?',
                'type': 'select',
                'options': ['None', 'Low', 'Moderate', 'High'],
                'required': True
            },
            {
                'category': 'Safety',
                'question': 'Do you feel safe at home and school?',
                'type': 'select',
                'options': ['Always safe', 'Usually safe', 'Sometimes unsafe', 'Often unsafe'],
                'required': True
            }
        ],
        'guidelines': """
        # Youth-Focused Listening Guidelines
        
        ## Special Considerations for Youth
        
        1. **Use age-appropriate language** - Adjust your vocabulary to match the youth's developmental level
        2. **Consider confidentiality limits** - Clearly explain when information must be shared (safety concerns)
        3. **Be authentic** - Youth can detect insincerity quickly
        4. **Allow autonomy** - Give choices when possible to help them feel empowered
        5. **Limit distractions** - Create an environment conducive to conversation
        
        ## Engagement Techniques
        
        - Start with less sensitive topics to build rapport
        - Use their language and terminology when appropriate
        - Show genuine curiosity about their experiences
        - Acknowledge their expertise about their own life
        - Normalize their experiences when appropriate
        - Validate their feelings without minimizing them
        
        ## Risk Assessment for Youth
        
        When assessing risk:
        
        - Watch for warning signs of suicide risk (withdrawal, giving away possessions, etc.)
        - Be direct when asking about self-harm or suicidal thoughts
        - Assess for bullying, abuse, or other safety concerns
        - Consider online safety and cyberbullying
        - Involve parents/guardians when appropriate for safety
        
        ## Closing the Session
        
        - Summarize strengths and resources you've identified
        - Discuss specific next steps
        - Provide resources that are youth-friendly
        - Explain what will happen next in concrete terms
        - End on a note of hope and capability
        """
    }
    
    # Store templates in database
    templates = [pfa_listening, youth_listening]
    imported_count = 0
    
    for template in templates:
        result = save_listening_template(template)
        if result:
            imported_count += 1
    
    return imported_count

def main():
    st.title("Listening Module Management")
    
    # Check database connection
    connection_status, _ = test_database_connection()
    if not connection_status:
        st.error("Database connection failed. Please check your database settings.")
        return
    
    # Sidebar for navigation
    st.sidebar.title("Actions")
    action = st.sidebar.radio("Choose an action", [
        "View Listening Templates", 
        "Add New Template", 
        "Edit Template", 
        "Delete Template",
        "Import Default Templates"
    ])
    
    if action == "View Listening Templates":
        st.header("Available Listening Templates")
        templates = get_all_listening_templates()
        
        if not templates:
            st.info("No listening templates found in the database. Add a new template or import default templates to get started.")
        else:
            # Display as a table
            templates_table = []
            for template in templates:
                question_count = len(template.get('questions', [])) if isinstance(template.get('questions', []), list) else 0
                templates_table.append({
                    "ID": template['id'],
                    "Name": template['name'],
                    "Questions": question_count,
                    "Last Updated": template.get('updated_at', '')
                })
            
            df = pd.DataFrame(templates_table)
            st.dataframe(df, use_container_width=True)
            
            # Display detailed information for a selected template
            if templates:
                template_ids = {t['id']: t['name'] for t in templates}
                selected_id = st.selectbox("Select a template to view details", 
                                          options=list(template_ids.keys()),
                                          format_func=lambda x: template_ids[x])
                
                selected_template = next((t for t in templates if t['id'] == selected_id), None)
                
                if selected_template:
                    st.subheader(f"Details for {selected_template['name']}")
                    
                    with st.expander("Description", expanded=True):
                        st.write(selected_template['description'])
                    
                    with st.expander("Questions", expanded=True):
                        questions = selected_template.get('questions', [])
                        if isinstance(questions, list):
                            # Group questions by category
                            questions_by_category = {}
                            for q in questions:
                                if isinstance(q, dict):
                                    category = q.get('category', 'General')
                                    if category not in questions_by_category:
                                        questions_by_category[category] = []
                                    questions_by_category[category].append(q)
                            
                            # Display questions grouped by category
                            for category, category_questions in questions_by_category.items():
                                st.markdown(f"### {category}")
                                for i, q in enumerate(category_questions, 1):
                                    st.write(f"{i}. {q.get('question', '')}")
                                    st.write(f"   *Type: {q.get('type', 'text')}*")
                                    
                                    if q.get('type') == 'select' and 'options' in q:
                                        st.write("   Options:")
                                        for opt in q['options']:
                                            st.write(f"   - {opt}")
                                    
                                    if q.get('required', False):
                                        st.write("   *Required*")
                                    st.write("")
                        else:
                            st.write("No questions available")
                    
                    with st.expander("Guidelines"):
                        st.markdown(selected_template.get('guidelines', 'No guidelines available'))
    
    elif action == "Add New Template":
        st.header("Add New Listening Template")
        
        with st.form("add_template_form"):
            name = st.text_input("Template Name")
            description = st.text_area("Description")
            
            # Questions - Use a structured approach with JSON
            st.subheader("Questions")
            st.markdown("""
            Enter questions in JSON format. Example:
            ```
            [
                {
                    "category": "Presenting Problems",
                    "question": "What brings you here today?",
                    "type": "text",
                    "required": true
                },
                {
                    "category": "Emotional State",
                    "question": "How are you feeling?",
                    "type": "select",
                    "options": ["Happy", "Sad", "Angry", "Anxious"],
                    "required": false
                }
            ]
            ```
            """)
            
            questions_json = st.text_area("Questions (JSON format)", height=300)
            
            guidelines = st.text_area("Guidelines (Markdown format)", 
                                    placeholder="Enter guidelines for conducting the listening session using markdown format")
            
            submitted = st.form_submit_button("Add Listening Template")
            
            if submitted:
                if not name or not questions_json:
                    st.error("Name and questions are required fields")
                else:
                    try:
                        # Parse questions JSON
                        questions = json.loads(questions_json)
                        
                        # Validate questions format
                        if not isinstance(questions, list):
                            st.error("Questions must be a JSON array/list")
                            return
                        
                        # Construct the template data
                        template_data = {
                            'name': name,
                            'description': description,
                            'questions': questions,
                            'guidelines': guidelines
                        }
                        
                        result = save_listening_template(template_data)
                        if result:
                            st.success(f"Listening template '{name}' added successfully with ID: {result}")
                        else:
                            st.error("Failed to add listening template")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format for questions. Please check your syntax.")
    
    elif action == "Edit Template":
        st.header("Edit Listening Template")
        
        templates = get_all_listening_templates()
        if not templates:
            st.info("No listening templates found in the database.")
            return
        
        # Select template to edit
        template_ids = {t['id']: t['name'] for t in templates}
        selected_id = st.selectbox("Select a template to edit", 
                                  options=list(template_ids.keys()),
                                  format_func=lambda x: template_ids[x])
        
        selected_template = next((t for t in templates if t['id'] == selected_id), None)
        
        if selected_template:
            with st.form("edit_template_form"):
                name = st.text_input("Template Name", value=selected_template['name'])
                description = st.text_area("Description", value=selected_template['description'])
                
                # Convert questions to JSON for editing
                questions_json = json.dumps(selected_template.get('questions', []), indent=2)
                
                st.subheader("Questions (JSON format)")
                questions_json = st.text_area("Questions", value=questions_json, height=300)
                
                guidelines = st.text_area("Guidelines (Markdown format)", 
                                        value=selected_template.get('guidelines', ''))
                
                submitted = st.form_submit_button("Update Listening Template")
                
                if submitted:
                    if not name or not questions_json:
                        st.error("Name and questions are required fields")
                    else:
                        try:
                            # Parse questions JSON
                            questions = json.loads(questions_json)
                            
                            # Validate questions format
                            if not isinstance(questions, list):
                                st.error("Questions must be a JSON array/list")
                                return
                            
                            # Construct the template data
                            template_data = {
                                'name': name,
                                'description': description,
                                'questions': questions,
                                'guidelines': guidelines
                            }
                            
                            result = save_listening_template(template_data, selected_id)
                            if result:
                                st.success(f"Listening template '{name}' updated successfully")
                            else:
                                st.error("Failed to update listening template")
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format for questions. Please check your syntax.")
    
    elif action == "Delete Template":
        st.header("Delete Listening Template")
        st.warning("Caution: Deleting a template is permanent and cannot be undone.")
        
        templates = get_all_listening_templates()
        if not templates:
            st.info("No listening templates found in the database.")
            return
        
        # Select template to delete
        template_ids = {t['id']: t['name'] for t in templates}
        selected_id = st.selectbox("Select a template to delete", 
                                  options=list(template_ids.keys()),
                                  format_func=lambda x: template_ids[x])
        
        selected_template = next((t for t in templates if t['id'] == selected_id), None)
        
        if selected_template:
            st.write(f"You are about to delete: **{selected_template['name']}**")
            st.write(f"This template has {len(selected_template.get('questions', []))} questions.")
            
            # Confirmation
            if st.button("Confirm Deletion", type="primary"):
                success, message = delete_listening_template(selected_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    elif action == "Import Default Templates":
        st.header("Import Default Listening Templates")
        st.info("""
        This action will import the following pre-configured listening templates:
        
        1. Standard PFA Listening Session
        2. Youth-Focused Listening Session
        
        If these templates already exist in the database, duplicates will be created.
        """)
        
        if st.button("Import Default Templates", type="primary"):
            imported_count = import_default_templates()
            if imported_count > 0:
                st.success(f"Successfully imported {imported_count} default listening templates")
            else:
                st.error("Failed to import default templates")

if __name__ == "__main__":
    main()