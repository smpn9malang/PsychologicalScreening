import streamlit as st
import datetime
from utils.database import save_patient, get_patient, get_patients
from utils.constants import get_referral_options

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

def main():
    st.title("Referral System (Link)")
    
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
                st.subheader("Risk Assessment")
                if patient_data.get('suicide_risk'):
                    st.write(f"**Suicide Risk:** {patient_data.get('suicide_risk')}")
                if patient_data.get('harm_risk'):
                    st.write(f"**Harm to Others Risk:** {patient_data.get('harm_risk')}")
                
                high_risk = patient_data.get('high_risk', False)
                if high_risk:
                    st.warning("⚠️ HIGH RISK ALERT: Immediate professional intervention recommended.")
            
            with col2:
                st.subheader("Screening Results")
                if patient_data.get('srq_complete', False):
                    st.write(f"**SRQ-20 Score:** {patient_data.get('srq_score')}/20")
                    if patient_data.get('srq_score', 0) >= 8:
                        st.warning("SRQ indicates need for mental health referral.")
                
                if patient_data.get('dass_complete', False):
                    st.write(f"**DASS-42 Depression:** {patient_data.get('dass_depression_score')} - {patient_data.get('dass_depression_severity')}")
                    st.write(f"**DASS-42 Anxiety:** {patient_data.get('dass_anxiety_score')} - {patient_data.get('dass_anxiety_severity')}")
                    st.write(f"**DASS-42 Stress:** {patient_data.get('dass_stress_score')} - {patient_data.get('dass_stress_severity')}")
        
        # Get referral options
        referral_options = get_referral_options()
        
        # Referral Form
        with st.form("referral_form"):
            st.subheader("Referral Information")
            
            # Pre-fill form if data exists
            referral_needed = st.checkbox("Referral Needed", 
                                        value=patient_data.get('referral_needed', False))
            
            if referral_needed:
                col1, col2 = st.columns(2)
                
                with col1:
                    referral_type = st.selectbox(
                        "Referral Type",
                        ["Mental Health Professional", "Healthcare Provider", "Crisis Services", "Social Services", "School Counselor", "Other"],
                        index=["Mental Health Professional", "Healthcare Provider", "Crisis Services", "Social Services", "School Counselor", "Other"].index(patient_data.get('referral_type', 'Mental Health Professional')) if patient_data.get('referral_type') else 0
                    )
                
                with col2:
                    referral_urgency = st.selectbox(
                        "Urgency",
                        ["Emergency (Immediate)", "Urgent (24-48 hours)", "Standard (1-2 weeks)", "Routine"],
                        index=["Emergency (Immediate)", "Urgent (24-48 hours)", "Standard (1-2 weeks)", "Routine"].index(patient_data.get('referral_urgency', 'Standard (1-2 weeks)')) if patient_data.get('referral_urgency') else 2
                    )
                
                # Select referral provider
                if referral_type in referral_options:
                    provider_options = referral_options[referral_type]
                    referral_provider = st.selectbox(
                        "Referral Provider",
                        provider_options,
                        index=provider_options.index(patient_data.get('referral_provider')) if patient_data.get('referral_provider') in provider_options else 0
                    )
                else:
                    referral_provider = st.text_input(
                        "Referral Provider (name or organization)",
                        value=patient_data.get('referral_provider', '')
                    )
                
                referral_contact_info = st.text_input(
                    "Contact Information",
                    value=patient_data.get('referral_contact_info', '')
                )
                
                referral_reason = st.text_area(
                    "Reason for Referral",
                    value=patient_data.get('referral_reason', '')
                )
            else:
                referral_type = ""
                referral_urgency = ""
                referral_provider = ""
                referral_contact_info = ""
                referral_reason = ""
            
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
                # Prepare referral data
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
                    
                    referral_data.update({
                        'referral_type': referral_type,
                        'referral_urgency': referral_urgency,
                        'referral_provider': referral_provider,
                        'referral_contact_info': referral_contact_info,
                        'referral_reason': referral_reason
                    })
                
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
