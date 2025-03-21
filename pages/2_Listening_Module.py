import streamlit as st
import datetime
from utils.database import save_patient, get_patient, get_patients

st.set_page_config(
    page_title="Listening Module - PFA Counseling",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state if needed
if 'current_patient_id' not in st.session_state:
    st.session_state.current_patient_id = None

def update_patient_listening_data(patient_data):
    """Update patient with listening module data"""
    patient_id = st.session_state.current_patient_id
    
    if not patient_id:
        st.error("No patient selected. Please complete patient assessment first.")
        return None
    
    existing_data = get_patient(patient_id)
    if existing_data:
        # Update only the listening module fields
        existing_data.update(patient_data)
        existing_data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing_data['listen_complete'] = True
        existing_data['assessment_step'] = 'listen'
        
        save_patient(patient_id, existing_data)
        return patient_id
    else:
        st.error("Patient data not found. Please complete patient assessment first.")
        return None

def main():
    st.title("Listening Module")
    
    # Sidebar for patient selection
    st.sidebar.title("Patient Selection")
    patients = get_patients()
    
    if not patients:
        st.info("No patients in the database. Please complete patient assessment first.")
        if st.button("Go to Patient Assessment"):
            st.switch_page("pages/1_Patient_Assessment.py")
        return
    
    # Filter to show only patients with completed 'look' assessment
    look_completed_patients = [p for p in patients if p.get('look_complete', False)]
    
    if not look_completed_patients:
        st.info("No patients with completed initial assessment. Please complete patient assessment first.")
        if st.button("Go to Patient Assessment"):
            st.switch_page("pages/1_Patient_Assessment.py")
        return
    
    patient_options = [f"{p['name']} (ID: {p['id']})" for p in look_completed_patients]
    selected_patient = st.sidebar.selectbox("Select a patient", patient_options)
    
    # Extract patient ID from selection
    patient_id = selected_patient.split("ID: ")[1].rstrip(")")
    st.session_state.current_patient_id = patient_id
    
    # Load patient data
    patient_data = get_patient(patient_id)
    
    if patient_data:
        st.info(f"Listening to: {patient_data.get('name', '')}, {patient_data.get('age', '')} years old")
        
        # Display patient's physical assessment summary
        with st.expander("View Physical Assessment Summary"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Appearance:** {patient_data.get('appearance', 'Not recorded')}")
            with col2:
                st.write(f"**Eye Contact:** {patient_data.get('eye_contact', 'Not recorded')}")
            with col3:
                st.write(f"**Demeanor/Affect:** {patient_data.get('demeanor', 'Not recorded')}")
            
            if patient_data.get('visible_distress', False):
                st.write(f"**Signs of Distress:** {', '.join(patient_data.get('distress_signs', ['None']))}")
            
            if patient_data.get('immediate_concerns'):
                st.write(f"**Immediate Concerns:** {patient_data.get('immediate_concerns')}")
            
            if patient_data.get('physical_notes'):
                st.write(f"**Additional Notes:** {patient_data.get('physical_notes')}")
        
        # Listening Module Form
        with st.form("listening_module_form"):
            st.subheader("Patient Narrative")
            
            # Pre-fill form if data exists
            chief_complaint = st.text_area("Chief Complaint/Primary Concern", 
                                         height=100,
                                         value=patient_data.get('chief_complaint', ''))
            
            narrative = st.text_area("Patient's Narrative (Key points from their story)", 
                                   height=200,
                                   value=patient_data.get('narrative', ''))
            
            st.subheader("Emotion Assessment")
            
            col1, col2 = st.columns(2)
            with col1:
                primary_emotion = st.selectbox("Primary Emotion Observed", 
                                             ["Anxiety", "Fear", "Sadness", "Grief", "Anger", "Guilt", "Shame", "Confusion", "Numbness", "Relief", "Other"],
                                             index=["Anxiety", "Fear", "Sadness", "Grief", "Anger", "Guilt", "Shame", "Confusion", "Numbness", "Relief", "Other"].index(patient_data.get('primary_emotion', 'Anxiety')) if patient_data.get('primary_emotion') else 0)
            
            with col2:
                emotional_intensity = st.slider("Emotional Intensity", 
                                              min_value=1, max_value=10, 
                                              value=patient_data.get('emotional_intensity', 5),
                                              help="1 = Minimal, 10 = Extreme")
            
            st.subheader("Support Assessment")
            
            support_systems = st.multiselect("Available Support Systems", 
                                           ["Family", "Friends", "Religious/Spiritual", "Community", "Professional", "None"],
                                           default=patient_data.get('support_systems', []))
            
            coping_strategies = st.text_area("Current Coping Strategies", 
                                          value=patient_data.get('coping_strategies', ''))
            
            st.subheader("Risk Assessment")
            
            col1, col2 = st.columns(2)
            with col1:
                suicide_risk = st.selectbox("Suicide Risk Assessment", 
                                          ["None indicated", "Passive thoughts", "Active ideation without plan", "Active ideation with plan", "Recent attempt"],
                                          index=["None indicated", "Passive thoughts", "Active ideation without plan", "Active ideation with plan", "Recent attempt"].index(patient_data.get('suicide_risk', 'None indicated')) if patient_data.get('suicide_risk') else 0)
            
            with col2:
                harm_risk = st.selectbox("Risk of Harm to Others", 
                                       ["None indicated", "Low", "Moderate", "High"],
                                       index=["None indicated", "Low", "Moderate", "High"].index(patient_data.get('harm_risk', 'None indicated')) if patient_data.get('harm_risk') else 0)
            
            st.subheader("Additional Notes")
            counselor_notes = st.text_area("Counselor's Notes and Observations", 
                                         value=patient_data.get('counselor_notes', ''))
            
            # Submit button
            submitted = st.form_submit_button("Save Listening Assessment")
            
            if submitted:
                if not chief_complaint or not narrative:
                    st.error("Please provide the chief complaint and patient narrative.")
                else:
                    # High risk flag for suicide or harm risk
                    high_risk = (
                        suicide_risk in ["Active ideation with plan", "Recent attempt"] or 
                        harm_risk in ["Moderate", "High"]
                    )
                    
                    # Prepare patient data
                    listening_data = {
                        'chief_complaint': chief_complaint,
                        'narrative': narrative,
                        'primary_emotion': primary_emotion,
                        'emotional_intensity': emotional_intensity,
                        'support_systems': support_systems,
                        'coping_strategies': coping_strategies,
                        'suicide_risk': suicide_risk,
                        'harm_risk': harm_risk,
                        'counselor_notes': counselor_notes,
                        'high_risk': high_risk
                    }
                    
                    # Save patient data
                    update_patient_listening_data(listening_data)
                    
                    st.success("Listening assessment saved successfully.")
                    
                    if high_risk:
                        st.warning("⚠️ HIGH RISK ALERT: This patient shows indicators of being at high risk. Immediate professional intervention may be necessary.")
                    
                    st.info("Proceed to the Screening Tools to continue the assessment.")
        
        # Add navigation buttons outside of the form
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back to Patient Assessment"):
                st.switch_page("pages/1_Patient_Assessment.py")
        with col2:
            if st.button("Continue to Screening Tools"):
                st.switch_page("pages/3_Screening_Tools.py")

if __name__ == "__main__":
    main()
