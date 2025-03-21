import streamlit as st
import datetime
import pandas as pd
from utils.database import save_patient, get_patient, get_patients
import uuid

st.set_page_config(
    page_title="Patient Assessment - PFA Counseling",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'current_patient_id' not in st.session_state:
    st.session_state.current_patient_id = None

def create_or_update_patient(patient_data):
    """Create or update a patient record"""
    patient_id = st.session_state.current_patient_id
    
    if not patient_id:
        # Create new patient
        patient_id = str(uuid.uuid4())
        patient_data['id'] = patient_id
        patient_data['created_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Update existing patient
        existing_data = get_patient(patient_id)
        if existing_data:
            patient_data['created_at'] = existing_data.get('created_at')
            
    patient_data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_patient(patient_id, patient_data)
    st.session_state.current_patient_id = patient_id
    return patient_id

def main():
    st.title("Patient Assessment (Look)")
    
    # Sidebar for existing patients
    st.sidebar.title("Existing Patients")
    patients = get_patients()
    
    if patients:
        patient_options = ["New Patient"] + [f"{p['name']} (ID: {p['id']})" for p in patients]
        selected_patient = st.sidebar.selectbox("Select a patient", patient_options)
        
        if selected_patient != "New Patient":
            # Extract patient ID from selection
            patient_id = selected_patient.split("ID: ")[1].rstrip(")")
            st.session_state.current_patient_id = patient_id
            
            # Load patient data
            patient_data = get_patient(patient_id)
            if patient_data:
                st.info(f"Editing patient: {patient_data.get('name', '')}")
        else:
            st.session_state.current_patient_id = None
    else:
        st.sidebar.info("No existing patients found.")
        st.session_state.current_patient_id = None
    
    # Form for patient assessment
    with st.form("patient_assessment_form"):
        st.subheader("Basic Information")
        col1, col2, col3 = st.columns(3)
        
        # If editing, pre-fill the form
        patient_data = get_patient(st.session_state.current_patient_id) if st.session_state.current_patient_id else {}
        
        with col1:
            name = st.text_input("Full Name", value=patient_data.get('name', ''))
        with col2:
            age = st.number_input("Age", min_value=1, max_value=120, value=int(patient_data.get('age', 25)))
        with col3:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                 index=["Male", "Female", "Other"].index(patient_data.get('gender', 'Male')) if patient_data.get('gender') else 0)
        
        st.subheader("Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input("Phone Number", value=patient_data.get('phone', ''))
        with col2:
            emergency_contact = st.text_input("Emergency Contact", value=patient_data.get('emergency_contact', ''))
        
        st.subheader("Physical Assessment (Look)")
        
        col1, col2 = st.columns(2)
        with col1:
            appearance = st.selectbox("Overall Appearance", 
                                     ["Normal", "Disheveled", "Well-groomed", "Unkempt", "Agitated", "Lethargic"],
                                     index=["Normal", "Disheveled", "Well-groomed", "Unkempt", "Agitated", "Lethargic"].index(patient_data.get('appearance', 'Normal')) if patient_data.get('appearance') else 0)
        with col2:
            eye_contact = st.selectbox("Eye Contact", 
                                      ["Normal", "Avoidant", "Intense", "Minimal", "Absent"],
                                      index=["Normal", "Avoidant", "Intense", "Minimal", "Absent"].index(patient_data.get('eye_contact', 'Normal')) if patient_data.get('eye_contact') else 0)
        
        demeanor = st.selectbox("Demeanor/Affect", 
                               ["Calm", "Anxious", "Depressed", "Irritable", "Flat", "Labile", "Euphoric", "Confused"],
                               index=["Calm", "Anxious", "Depressed", "Irritable", "Flat", "Labile", "Euphoric", "Confused"].index(patient_data.get('demeanor', 'Calm')) if patient_data.get('demeanor') else 0)
        
        visible_distress = st.checkbox("Signs of Visible Distress", value=patient_data.get('visible_distress', False))
        
        if visible_distress:
            distress_signs = st.multiselect("Signs of Distress", 
                                          ["Crying", "Trembling", "Sweating", "Rapid breathing", "Pacing", "Self-harm marks", "Other"],
                                          default=patient_data.get('distress_signs', []))
        else:
            distress_signs = []
        
        st.subheader("Initial Observations")
        immediate_concerns = st.text_area("Immediate Concerns or Needs", value=patient_data.get('immediate_concerns', ''))
        physical_notes = st.text_area("Additional Physical Assessment Notes", value=patient_data.get('physical_notes', ''))
        
        # Submit button
        submitted = st.form_submit_button("Save Assessment")
        
        if submitted:
            if not name:
                st.error("Patient name is required.")
            else:
                # Prepare patient data
                patient_data = {
                    'name': name,
                    'age': age,
                    'gender': gender,
                    'phone': phone,
                    'emergency_contact': emergency_contact,
                    'appearance': appearance,
                    'eye_contact': eye_contact,
                    'demeanor': demeanor,
                    'visible_distress': visible_distress,
                    'distress_signs': distress_signs if visible_distress else [],
                    'immediate_concerns': immediate_concerns,
                    'physical_notes': physical_notes,
                    'assessment_step': 'look',
                    'look_complete': True
                }
                
                # Save patient data
                patient_id = create_or_update_patient(patient_data)
                
                st.success(f"Assessment saved successfully for {name}.")
                st.info("Proceed to the Listening Module to continue the assessment.")
                
                # Add a continue button
                if st.button("Continue to Listening Module"):
                    st.switch_page("pages/2_Listening_Module.py")

if __name__ == "__main__":
    main()
