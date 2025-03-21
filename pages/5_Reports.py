import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import get_patients, get_patient
import datetime

st.set_page_config(
    page_title="Reports - PFA Counseling",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state if needed
if 'current_patient_id' not in st.session_state:
    st.session_state.current_patient_id = None

def generate_individual_report(patient_data):
    """Generate comprehensive report for an individual patient"""
    st.header(f"Patient Report: {patient_data.get('name')}")
    
    # Basic information section
    st.subheader("Basic Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Name:** {patient_data.get('name')}")
        st.write(f"**Age:** {patient_data.get('age')}")
        st.write(f"**Gender:** {patient_data.get('gender')}")
    with col2:
        st.write(f"**Phone:** {patient_data.get('phone')}")
        st.write(f"**Emergency Contact:** {patient_data.get('emergency_contact')}")
    with col3:
        st.write(f"**Assessment Date:** {patient_data.get('created_at')}")
        st.write(f"**Last Updated:** {patient_data.get('last_updated')}")
    
    # Physical assessment
    st.subheader("Physical Assessment (Look)")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Appearance:** {patient_data.get('appearance')}")
        st.write(f"**Eye Contact:** {patient_data.get('eye_contact')}")
        st.write(f"**Demeanor/Affect:** {patient_data.get('demeanor')}")
    with col2:
        if patient_data.get('visible_distress'):
            st.write(f"**Signs of Distress:** {', '.join(patient_data.get('distress_signs', []))}")
        if patient_data.get('immediate_concerns'):
            st.write(f"**Immediate Concerns:** {patient_data.get('immediate_concerns')}")
    
    if patient_data.get('physical_notes'):
        st.write(f"**Additional Notes:** {patient_data.get('physical_notes')}")
    
    # Listening assessment
    if patient_data.get('listen_complete'):
        st.subheader("Listening Assessment")
        
        st.write(f"**Chief Complaint:** {patient_data.get('chief_complaint')}")
        
        with st.expander("Patient Narrative"):
            st.write(patient_data.get('narrative', 'No narrative recorded'))
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Primary Emotion:** {patient_data.get('primary_emotion')}")
            st.write(f"**Emotional Intensity:** {patient_data.get('emotional_intensity')}/10")
        with col2:
            st.write(f"**Support Systems:** {', '.join(patient_data.get('support_systems', []))}")
            st.write(f"**Coping Strategies:** {patient_data.get('coping_strategies')}")
        
        # Risk assessment
        st.write("**Risk Assessment:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Suicide Risk:** {patient_data.get('suicide_risk')}")
        with col2:
            st.write(f"**Risk of Harm to Others:** {patient_data.get('harm_risk')}")
        
        if patient_data.get('counselor_notes'):
            st.write(f"**Counselor's Notes:** {patient_data.get('counselor_notes')}")
    
    # Screening results
    if patient_data.get('screening_complete'):
        st.subheader("Screening Results")
        
        # SRQ results
        if patient_data.get('srq_complete'):
            st.write(f"**SRQ-20 Score:** {patient_data.get('srq_score')}/20")
            
            # Interpret SRQ score
            srq_score = patient_data.get('srq_score', 0)
            if srq_score >= 11:
                st.error("SRQ Interpretation: Severe mental distress indicated")
            elif srq_score >= 8:
                st.warning("SRQ Interpretation: Moderate mental distress indicated")
            elif srq_score >= 5:
                st.info("SRQ Interpretation: Mild mental distress indicated")
            else:
                st.success("SRQ Interpretation: No significant mental distress indicated")
        
        # DASS-42 results
        if patient_data.get('dass_complete'):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Depression", f"{patient_data.get('dass_depression_score')} - {patient_data.get('dass_depression_severity')}")
            with col2:
                st.metric("Anxiety", f"{patient_data.get('dass_anxiety_score')} - {patient_data.get('dass_anxiety_severity')}")
            with col3:
                st.metric("Stress", f"{patient_data.get('dass_stress_score')} - {patient_data.get('dass_stress_severity')}")
            
            # Create a bar chart for visualization
            data = {
                'Category': ['Depression', 'Anxiety', 'Stress'],
                'Score': [
                    patient_data.get('dass_depression_score', 0), 
                    patient_data.get('dass_anxiety_score', 0), 
                    patient_data.get('dass_stress_score', 0)
                ]
            }
            df = pd.DataFrame(data)
            
            fig = px.bar(df, x='Category', y='Score', color='Category',
                        text_auto=True,
                        title="DASS-42 Scores")
            st.plotly_chart(fig)
    
    # Referral information
    if patient_data.get('referral_complete'):
        st.subheader("Referral Information")
        
        if patient_data.get('referral_needed'):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Referral Type:** {patient_data.get('referral_type')}")
                st.write(f"**Referral Provider:** {patient_data.get('referral_provider')}")
                st.write(f"**Contact Information:** {patient_data.get('referral_contact_info')}")
            with col2:
                st.write(f"**Urgency:** {patient_data.get('referral_urgency')}")
                st.write(f"**Reason for Referral:** {patient_data.get('referral_reason')}")
        else:
            st.info("No referral needed at this time.")
        
        st.write(f"**Follow-up Plan:** {patient_data.get('follow_up_plan')}")
        st.write(f"**Follow-up Date:** {patient_data.get('follow_up_date')}")
        
        if patient_data.get('additional_notes'):
            st.write(f"**Additional Notes:** {patient_data.get('additional_notes')}")
    
    # Assessment Status
    st.subheader("Assessment Status")
    
    # Create a list of assessment steps and their completion status
    steps = [
        {"name": "Look (Initial Assessment)", "complete": patient_data.get('look_complete', False)},
        {"name": "Listen (Patient Narrative)", "complete": patient_data.get('listen_complete', False)},
        {"name": "Screening Tools", "complete": patient_data.get('screening_complete', False)},
        {"name": "Link (Referral)", "complete": patient_data.get('referral_complete', False)}
    ]
    
    # Display as a progress bar
    completed_steps = sum(step["complete"] for step in steps)
    progress = completed_steps / len(steps)
    
    st.progress(progress)
    st.write(f"Assessment Progress: {completed_steps}/{len(steps)} steps completed")
    
    # Print button
    st.button("Print Report", on_click=lambda: st.balloons())

def generate_summary_report(patients):
    """Generate summary report of all patients"""
    st.header("Summary Report")
    
    # Basic statistics
    st.subheader("Patient Statistics")
    
    total_patients = len(patients)
    completed_assessments = sum(1 for p in patients if p.get('assessment_complete', False))
    referrals_needed = sum(1 for p in patients if p.get('referral_needed', False))
    high_risk_patients = sum(1 for p in patients if p.get('high_risk', False))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", total_patients)
    with col2:
        st.metric("Completed Assessments", completed_assessments)
    with col3:
        st.metric("Referrals Needed", referrals_needed)
    with col4:
        st.metric("High Risk Patients", high_risk_patients)
    
    # Demographics
    if total_patients > 0:
        st.subheader("Demographics")
        
        # Age distribution
        ages = [p.get('age', 0) for p in patients if p.get('age')]
        if ages:
            # Create age groups
            age_ranges = ["0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61+"]
            age_counts = [0] * len(age_ranges)
            
            for age in ages:
                if age <= 10:
                    age_counts[0] += 1
                elif age <= 20:
                    age_counts[1] += 1
                elif age <= 30:
                    age_counts[2] += 1
                elif age <= 40:
                    age_counts[3] += 1
                elif age <= 50:
                    age_counts[4] += 1
                elif age <= 60:
                    age_counts[5] += 1
                else:
                    age_counts[6] += 1
            
            age_data = pd.DataFrame({
                'Age Range': age_ranges,
                'Count': age_counts
            })
            
            fig = px.bar(age_data, x='Age Range', y='Count', title="Age Distribution")
            st.plotly_chart(fig)
        
        # Gender distribution
        genders = [p.get('gender', 'Unknown') for p in patients if p.get('gender')]
        if genders:
            gender_counts = {}
            for g in genders:
                gender_counts[g] = gender_counts.get(g, 0) + 1
            
            gender_data = pd.DataFrame({
                'Gender': list(gender_counts.keys()),
                'Count': list(gender_counts.values())
            })
            
            fig = px.pie(gender_data, names='Gender', values='Count', title="Gender Distribution")
            st.plotly_chart(fig)
        
        # Screening tool results summary
        st.subheader("Screening Tool Results")
        
        # SRQ scores
        srq_scores = [p.get('srq_score', 0) for p in patients if p.get('srq_complete', False)]
        if srq_scores:
            # Calculate severity categories
            srq_categories = {
                "Normal (0-4)": sum(1 for s in srq_scores if s < 5),
                "Mild (5-7)": sum(1 for s in srq_scores if 5 <= s < 8),
                "Moderate (8-10)": sum(1 for s in srq_scores if 8 <= s < 11),
                "Severe (11+)": sum(1 for s in srq_scores if s >= 11)
            }
            
            srq_data = pd.DataFrame({
                'Category': list(srq_categories.keys()),
                'Count': list(srq_categories.values())
            })
            
            fig = px.pie(srq_data, names='Category', values='Count', title="SRQ-20 Results Distribution")
            st.plotly_chart(fig)
        
        # DASS-42 scores
        dass_completed = [p for p in patients if p.get('dass_complete', False)]
        if dass_completed:
            # Extract depression, anxiety, and stress scores
            depression_data = {
                "Normal": sum(1 for p in dass_completed if p.get('dass_depression_severity') == "Normal"),
                "Mild": sum(1 for p in dass_completed if p.get('dass_depression_severity') == "Mild"),
                "Moderate": sum(1 for p in dass_completed if p.get('dass_depression_severity') == "Moderate"),
                "Severe": sum(1 for p in dass_completed if p.get('dass_depression_severity') == "Severe"),
                "Extremely Severe": sum(1 for p in dass_completed if p.get('dass_depression_severity') == "Extremely Severe")
            }
            
            anxiety_data = {
                "Normal": sum(1 for p in dass_completed if p.get('dass_anxiety_severity') == "Normal"),
                "Mild": sum(1 for p in dass_completed if p.get('dass_anxiety_severity') == "Mild"),
                "Moderate": sum(1 for p in dass_completed if p.get('dass_anxiety_severity') == "Moderate"),
                "Severe": sum(1 for p in dass_completed if p.get('dass_anxiety_severity') == "Severe"),
                "Extremely Severe": sum(1 for p in dass_completed if p.get('dass_anxiety_severity') == "Extremely Severe")
            }
            
            stress_data = {
                "Normal": sum(1 for p in dass_completed if p.get('dass_stress_severity') == "Normal"),
                "Mild": sum(1 for p in dass_completed if p.get('dass_stress_severity') == "Mild"),
                "Moderate": sum(1 for p in dass_completed if p.get('dass_stress_severity') == "Moderate"),
                "Severe": sum(1 for p in dass_completed if p.get('dass_stress_severity') == "Severe"),
                "Extremely Severe": sum(1 for p in dass_completed if p.get('dass_stress_severity') == "Extremely Severe")
            }
            
            # Create a grouped bar chart for DASS-42 results
            categories = ["Normal", "Mild", "Moderate", "Severe", "Extremely Severe"]
            
            fig = go.Figure(data=[
                go.Bar(name='Depression', x=categories, y=[depression_data[cat] for cat in categories]),
                go.Bar(name='Anxiety', x=categories, y=[anxiety_data[cat] for cat in categories]),
                go.Bar(name='Stress', x=categories, y=[stress_data[cat] for cat in categories])
            ])
            
            fig.update_layout(
                title="DASS-42 Results Distribution",
                xaxis_title="Severity Category",
                yaxis_title="Number of Patients",
                legend_title="Scale",
                barmode='group'
            )
            
            st.plotly_chart(fig)

def main():
    st.title("PFA Counseling Reports")
    
    # Sidebar for report selection
    st.sidebar.title("Report Options")
    
    report_type = st.sidebar.radio(
        "Report Type",
        ["Individual Patient Report", "Summary Report"]
    )
    
    # Get all patients
    patients = get_patients()
    
    if not patients:
        st.info("No patients in the database. Please complete patient assessments first.")
        if st.button("Go to Patient Assessment"):
            st.switch_page("pages/1_Patient_Assessment.py")
        return
    
    if report_type == "Individual Patient Report":
        st.sidebar.subheader("Select Patient")
        
        patient_options = [f"{p['name']} (ID: {p['id']})" for p in patients]
        selected_patient = st.sidebar.selectbox("Patient", patient_options)
        
        # Extract patient ID from selection
        patient_id = selected_patient.split("ID: ")[1].rstrip(")")
        st.session_state.current_patient_id = patient_id
        
        # Get patient data
        patient_data = get_patient(patient_id)
        
        if patient_data:
            generate_individual_report(patient_data)
        else:
            st.error("Patient data not found.")
    
    elif report_type == "Summary Report":
        generate_summary_report(patients)

if __name__ == "__main__":
    main()
