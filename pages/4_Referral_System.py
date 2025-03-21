import streamlit as st
import datetime
import json
from utils.database import save_patient, get_patient, get_patients
from utils.constants import get_referral_options
from utils.db_connector import get_db_connection, test_database_connection

st.set_page_config(
    page_title="Referral System - PFA Counseling",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state if needed
if 'current_patient_id' not in st.session_state:
    st.session_state.current_patient_id = None

def update_patient_referral_data(referral_data):
    """Update patient with referral data"""
    patient_id = st.session_state.current_patient_id
    
    if not patient_id:
        st.error("No patient selected. Please complete previous assessments first.")
        return None
    
    existing_data = get_patient(patient_id)
    if existing_data:
        # Update only the referral fields
        existing_data.update(referral_data)
        existing_data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing_data['referral_complete'] = True
        existing_data['assessment_complete'] = True
        existing_data['assessment_step'] = 'complete'
        
        save_patient(patient_id, existing_data)
        return patient_id
    else:
        st.error("Patient data not found. Please complete previous assessments first.")
        return None

def create_database_referral(referral_data):
    """Create a new referral record in the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Insert new referral
                cur.execute("""
                    INSERT INTO referrals 
                    (patient_id, consultant_id, psychiatrist_id, reason, notes, status, appointment_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    referral_data['patient_id'],
                    referral_data.get('consultant_id'),
                    referral_data.get('psychiatrist_id'),
                    referral_data['reason'],
                    referral_data.get('notes', ''),
                    referral_data.get('status', 'pending'),
                    referral_data.get('appointment_date')
                ))
                
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            st.error(f"Error creating referral: {e}")
        finally:
            conn.close()
    return None

def get_all_consultants():
    """Get all mental health consultants from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM consultants ORDER BY name ASC")
                columns = [desc[0] for desc in cur.description]
                result = cur.fetchall()
                
                # Convert to list of dictionaries
                consultants = []
                for row in result:
                    consultant_dict = dict(zip(columns, row))
                    
                    # Parse JSONB fields
                    if 'contact_info' in consultant_dict and consultant_dict['contact_info']:
                        consultant_dict['contact_info'] = json.loads(consultant_dict['contact_info'])
                    if 'availability' in consultant_dict and consultant_dict['availability']:
                        consultant_dict['availability'] = json.loads(consultant_dict['availability'])
                        
                    consultants.append(consultant_dict)
                
                return consultants
        except Exception as e:
            st.error(f"Error retrieving consultants: {e}")
        finally:
            conn.close()
    return []

def get_all_psychiatrists():
    """Get all psychiatrists from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM psychiatrists ORDER BY name ASC")
                columns = [desc[0] for desc in cur.description]
                result = cur.fetchall()
                
                # Convert to list of dictionaries
                psychiatrists = []
                for row in result:
                    psychiatrist_dict = dict(zip(columns, row))
                    
                    # Parse JSONB fields
                    if 'contact_info' in psychiatrist_dict and psychiatrist_dict['contact_info']:
                        psychiatrist_dict['contact_info'] = json.loads(psychiatrist_dict['contact_info'])
                    if 'availability' in psychiatrist_dict and psychiatrist_dict['availability']:
                        psychiatrist_dict['availability'] = json.loads(psychiatrist_dict['availability'])
                        
                    psychiatrists.append(psychiatrist_dict)
                
                return psychiatrists
        except Exception as e:
            st.error(f"Error retrieving psychiatrists: {e}")
        finally:
            conn.close()
    return []

def get_patients_referrals(patient_id):
    """Get all referrals for a specific patient from the database"""
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
                    WHERE r.patient_id = %s
                    ORDER BY r.created_at DESC
                """, (patient_id,))
                
                columns = [desc[0] for desc in cur.description]
                result = cur.fetchall()
                
                # Convert to list of dictionaries
                referrals = []
                for row in result:
                    referral_dict = dict(zip(columns, row))
                    referrals.append(referral_dict)
                
                return referrals
        except Exception as e:
            st.error(f"Error retrieving patient referrals: {e}")
        finally:
            conn.close()
    return []

def main():
    st.title("Referral System (Link)")
    
    # Check database connection
    connection_status, _ = test_database_connection()
    if not connection_status:
        st.error("Database connection failed. Please check your database settings.")
        return
    
    # Sidebar for patient selection
    st.sidebar.title("Patient Selection")
    patients = get_patients()
    
    if not patients:
        st.info("No patients in the database. Please complete patient assessment first.")
        if st.button("Go to Patient Assessment"):
            st.switch_page("pages/1_Patient_Assessment.py")
        return
    
    # Filter to show only patients with completed 'screening' assessment
    screening_completed_patients = [p for p in patients if p.get('screening_complete', False)]
    
    if not screening_completed_patients:
        st.info("No patients with completed screening assessment. Please complete the screening tools first.")
        if st.button("Go to Screening Tools"):
            st.switch_page("pages/3_Screening_Tools.py")
        return
    
    patient_options = [f"{p['name']} (ID: {p['id']})" for p in screening_completed_patients]
    selected_patient = st.sidebar.selectbox("Select a patient", patient_options)
    
    # Extract patient ID from selection
    patient_id = selected_patient.split("ID: ")[1].rstrip(")")
    st.session_state.current_patient_id = patient_id
    
    # Load patient data
    patient_data = get_patient(patient_id)
    
    if patient_data:
        st.info(f"Creating referral for: {patient_data.get('name', '')}, {patient_data.get('age', '')} years old")
        
        # Display screening results summary
        with st.expander("Assessment Summary", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Screening Results")
                
                # SRQ-20 Score
                if 'srq20_score' in patient_data:
                    st.markdown(f"**SRQ-20 Score:** {patient_data['srq20_score']}/20")
                    
                    # Add interpretation
                    if patient_data['srq20_score'] <= 4:
                        st.markdown("📊 **Interpretation:** No significant mental distress")
                    elif patient_data['srq20_score'] <= 7:
                        st.markdown("📊 **Interpretation:** Mild mental distress")
                    elif patient_data['srq20_score'] <= 10:
                        st.markdown("📊 **Interpretation:** Moderate mental distress")
                    else:
                        st.markdown("📊 **Interpretation:** Severe mental distress")
                
                # SRQ-29 Score
                if 'srq29_score' in patient_data:
                    st.markdown(f"**SRQ-29 Score:** {patient_data['srq29_score']}/29")
                    
                    if 'srq29_subscale_scores' in patient_data:
                        subscales = patient_data['srq29_subscale_scores']
                        st.markdown(f"- Anxiety/Depression: {subscales.get('anxiety_depression', 0)}/20")
                        st.markdown(f"- Psychotic Symptoms: {subscales.get('psychotic', 0)}/4")
                        st.markdown(f"- Epilepsy: {subscales.get('epilepsy', 0)}/1")
                        st.markdown(f"- Alcohol: {subscales.get('alcohol', 0)}/4")
                
                # DASS-42 Scores
                if 'dass42_scores' in patient_data:
                    scores = patient_data['dass42_scores']
                    st.markdown("**DASS-42 Scores:**")
                    
                    depression = scores.get('depression', 0)
                    st.markdown(f"- Depression: {depression}/42")
                    if depression <= 9:
                        st.markdown("  *Normal*")
                    elif depression <= 13:
                        st.markdown("  *Mild*")
                    elif depression <= 20:
                        st.markdown("  *Moderate*")
                    elif depression <= 27:
                        st.markdown("  *Severe*")
                    else:
                        st.markdown("  *Extremely Severe*")
                    
                    anxiety = scores.get('anxiety', 0)
                    st.markdown(f"- Anxiety: {anxiety}/42")
                    if anxiety <= 7:
                        st.markdown("  *Normal*")
                    elif anxiety <= 9:
                        st.markdown("  *Mild*")
                    elif anxiety <= 14:
                        st.markdown("  *Moderate*")
                    elif anxiety <= 19:
                        st.markdown("  *Severe*")
                    else:
                        st.markdown("  *Extremely Severe*")
                    
                    stress = scores.get('stress', 0)
                    st.markdown(f"- Stress: {stress}/42")
                    if stress <= 14:
                        st.markdown("  *Normal*")
                    elif stress <= 18:
                        st.markdown("  *Mild*")
                    elif stress <= 25:
                        st.markdown("  *Moderate*")
                    elif stress <= 33:
                        st.markdown("  *Severe*")
                    else:
                        st.markdown("  *Extremely Severe*")
            
            with col2:
                st.subheader("Patient Information")
                st.markdown(f"**Name:** {patient_data.get('name', 'N/A')}")
                st.markdown(f"**Age:** {patient_data.get('age', 'N/A')}")
                st.markdown(f"**Gender:** {patient_data.get('gender', 'N/A')}")
                st.markdown(f"**Contact:** {patient_data.get('contact', 'N/A')}")
                st.markdown(f"**Address:** {patient_data.get('address', 'N/A')}")
                
                if 'presenting_problems' in patient_data:
                    st.markdown(f"**Presenting Problems:** {patient_data['presenting_problems']}")
                
                if 'listening_notes' in patient_data:
                    st.markdown(f"**Listening Notes:** {patient_data['listening_notes']}")
        
        # Display previous referrals for this patient
        existing_referrals = get_patients_referrals(patient_id)
        if existing_referrals:
            with st.expander("Previous Referrals", expanded=True):
                for idx, ref in enumerate(existing_referrals):
                    st.markdown(f"### Referral #{idx+1} - {ref['created_at'].strftime('%Y-%m-%d')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if ref.get('consultant_name'):
                            st.markdown(f"**Consultant:** {ref['consultant_name']}")
                        if ref.get('psychiatrist_name'):
                            st.markdown(f"**Psychiatrist:** {ref['psychiatrist_name']}")
                        st.markdown(f"**Status:** {ref['status'].capitalize()}")
                    
                    with col2:
                        st.markdown(f"**Reason:** {ref['reason']}")
                        if ref.get('notes'):
                            st.markdown(f"**Notes:** {ref['notes']}")
                        if ref.get('appointment_date'):
                            st.markdown(f"**Appointment Date:** {ref['appointment_date'].strftime('%Y-%m-%d %H:%M')}")
                    
                    st.divider()
        
        # Get lists of consultants and psychiatrists
        consultants = get_all_consultants()
        psychiatrists = get_all_psychiatrists()
        
        # Referral Form
        with st.form("referral_form"):
            st.subheader("New Referral")
            
            # Pre-fill form if data exists
            referral_needed = st.checkbox("Referral Needed", 
                                        value=patient_data.get('referral_needed', False))
            
            if referral_needed:
                col1, col2 = st.columns(2)
                
                with col1:
                    referral_type = st.selectbox(
                        "Referral Type",
                        ["Mental Health Consultant", "Psychiatrist", "Both"]
                    )
                
                with col2:
                    referral_urgency = st.selectbox(
                        "Urgency",
                        ["Emergency (Immediate)", "Urgent (24-48 hours)", "Standard (1-2 weeks)", "Routine"],
                        index=2  # Default to Standard
                    )
                
                # Select referral provider based on type
                consultant_id = None
                psychiatrist_id = None
                
                if referral_type in ["Mental Health Consultant", "Both"] and consultants:
                    consultant_options = {c['id']: f"{c['name']} - {c['specialization']}" for c in consultants}
                    selected_consultant_id = st.selectbox(
                        "Select Mental Health Consultant",
                        options=list(consultant_options.keys()),
                        format_func=lambda x: consultant_options[x]
                    )
                    consultant_id = selected_consultant_id
                    
                    # Show selected consultant details
                    selected_consultant = next((c for c in consultants if c['id'] == selected_consultant_id), None)
                    if selected_consultant:
                        with st.expander("Consultant Details"):
                            st.write(f"**Name:** {selected_consultant['name']}")
                            st.write(f"**Specialization:** {selected_consultant['specialization']}")
                            st.write(f"**Qualifications:** {selected_consultant['qualifications']}")
                            
                            # Display contact info if available
                            contact_info = selected_consultant.get('contact_info', {})
                            if isinstance(contact_info, dict) and contact_info:
                                st.write("**Contact Information:**")
                                for key, value in contact_info.items():
                                    st.write(f"- {key.capitalize()}: {value}")
                
                if referral_type in ["Psychiatrist", "Both"] and psychiatrists:
                    psychiatrist_options = {p['id']: f"{p['name']} - {p['specialization']} ({p['hospital']})" for p in psychiatrists}
                    selected_psychiatrist_id = st.selectbox(
                        "Select Psychiatrist",
                        options=list(psychiatrist_options.keys()),
                        format_func=lambda x: psychiatrist_options[x]
                    )
                    psychiatrist_id = selected_psychiatrist_id
                    
                    # Show selected psychiatrist details
                    selected_psychiatrist = next((p for p in psychiatrists if p['id'] == selected_psychiatrist_id), None)
                    if selected_psychiatrist:
                        with st.expander("Psychiatrist Details"):
                            st.write(f"**Name:** {selected_psychiatrist['name']}")
                            st.write(f"**Specialization:** {selected_psychiatrist['specialization']}")
                            st.write(f"**Hospital/Clinic:** {selected_psychiatrist['hospital']}")
                            st.write(f"**Qualifications:** {selected_psychiatrist['qualifications']}")
                            
                            # Display contact info if available
                            contact_info = selected_psychiatrist.get('contact_info', {})
                            if isinstance(contact_info, dict) and contact_info:
                                st.write("**Contact Information:**")
                                for key, value in contact_info.items():
                                    st.write(f"- {key.capitalize()}: {value}")
                
                # Warning messages if no providers are available
                if referral_type in ["Mental Health Consultant", "Both"] and not consultants:
                    st.warning("No mental health consultants found in the database. Please add consultants in the Consultant Management page.")
                
                if referral_type in ["Psychiatrist", "Both"] and not psychiatrists:
                    st.warning("No psychiatrists found in the database. Please add psychiatrists in the Psychiatrist Management page.")
                
                referral_reason = st.text_area(
                    "Reason for Referral",
                    value=patient_data.get('referral_reason', '')
                )
                
                appointment_date = st.date_input(
                    "Tentative Appointment Date",
                    value=datetime.datetime.now().date() + datetime.timedelta(days=7)
                )
                
                appointment_time = st.time_input(
                    "Tentative Appointment Time",
                    value=datetime.time(9, 0)
                )
                
                appointment_datetime = datetime.datetime.combine(appointment_date, appointment_time)
            else:
                referral_type = ""
                referral_urgency = ""
                consultant_id = None
                psychiatrist_id = None
                referral_reason = ""
                appointment_datetime = None
            
            st.subheader("Follow-up Plan")
            
            follow_up_plan = st.text_area(
                "Follow-up Plan",
                value=patient_data.get('follow_up_plan', '')
            )
            
            follow_up_date = st.date_input(
                "Follow-up Date",
                value=datetime.datetime.strptime(patient_data.get('follow_up_date', datetime.datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
            )
            
            additional_notes = st.text_area(
                "Additional Notes",
                value=patient_data.get('additional_notes', '')
            )
            
            # Submit button
            submitted = st.form_submit_button("Save Referral Information")
            
            if submitted:
                # Prepare referral data for patient record
                referral_data = {
                    'referral_needed': referral_needed,
                    'follow_up_plan': follow_up_plan,
                    'follow_up_date': follow_up_date.strftime("%Y-%m-%d"),
                    'additional_notes': additional_notes
                }
                
                if referral_needed:
                    if not referral_reason:
                        st.error("Please provide a reason for the referral.")
                        return
                    
                    if referral_type == "Mental Health Consultant" and not consultant_id:
                        st.error("Please select a mental health consultant.")
                        return
                    
                    if referral_type == "Psychiatrist" and not psychiatrist_id:
                        st.error("Please select a psychiatrist.")
                        return
                    
                    if referral_type == "Both" and (not consultant_id or not psychiatrist_id):
                        st.error("Please select both a mental health consultant and a psychiatrist.")
                        return
                    
                    # Add referral details to patient record
                    referral_data.update({
                        'referral_type': referral_type,
                        'referral_urgency': referral_urgency,
                        'referral_reason': referral_reason
                    })
                    
                    # Create database referral
                    db_referral_data = {
                        'patient_id': patient_id,
                        'consultant_id': consultant_id if consultant_id and referral_type in ["Mental Health Consultant", "Both"] else None,
                        'psychiatrist_id': psychiatrist_id if psychiatrist_id and referral_type in ["Psychiatrist", "Both"] else None,
                        'reason': referral_reason,
                        'notes': additional_notes,
                        'status': 'pending',
                        'appointment_date': appointment_datetime if appointment_datetime else None
                    }
                    
                    referral_id = create_database_referral(db_referral_data)
                    if referral_id:
                        referral_data['database_referral_id'] = referral_id
                
                # Update patient data
                update_patient_referral_data(referral_data)
                
                st.success("Referral information saved successfully.")
                
                if referral_needed and referral_urgency in ["Emergency (Immediate)", "Urgent (24-48 hours)"]:
                    st.warning(f"⚠️ This is an {referral_urgency} referral. Please ensure the patient receives prompt care.")
                
                # Add a view reports button
                if st.button("View Patient Report"):
                    st.switch_page("pages/5_Reports.py")

if __name__ == "__main__":
    main()