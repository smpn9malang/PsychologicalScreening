import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import save_patient, get_patient, get_patients
from utils.screening_tools import (
    get_srq20_questions,
    get_srq29_questions,
    calculate_srq20_score,
    calculate_srq29_score,
    get_srq29_subscale_scores,
    get_dass42_questions,
    calculate_dass42_scores
)

st.set_page_config(
    page_title="Screening Tools - PFA Counseling",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state if needed
if 'current_patient_id' not in st.session_state:
    st.session_state.current_patient_id = None
if 'current_screening_tool' not in st.session_state:
    st.session_state.current_screening_tool = "SRQ-20"

def update_patient_screening_data(screening_data):
    """Update patient with screening data"""
    patient_id = st.session_state.current_patient_id
    
    if not patient_id:
        st.error("No patient selected. Please complete patient assessment first.")
        return None
    
    existing_data = get_patient(patient_id)
    if existing_data:
        # Update only the screening fields
        existing_data.update(screening_data)
        existing_data['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing_data['screening_complete'] = True
        existing_data['assessment_step'] = 'screening'
        
        save_patient(patient_id, existing_data)
        return patient_id
    else:
        st.error("Patient data not found. Please complete patient assessment first.")
        return None

def main():
    st.title("Screening Tools")
    
    # Sidebar for patient selection
    st.sidebar.title("Patient Selection")
    patients = get_patients()
    
    if not patients:
        st.info("No patients in the database. Please complete patient assessment first.")
        if st.button("Go to Patient Assessment"):
            st.switch_page("pages/1_Patient_Assessment.py")
        return
    
    # Filter to show only patients with completed 'listen' assessment
    listen_completed_patients = [p for p in patients if p.get('listen_complete', False)]
    
    if not listen_completed_patients:
        st.info("No patients with completed listening assessment. Please complete the listening module first.")
        if st.button("Go to Listening Module"):
            st.switch_page("pages/2_Listening_Module.py")
        return
    
    patient_options = [f"{p['name']} (ID: {p['id']})" for p in listen_completed_patients]
    selected_patient = st.sidebar.selectbox("Select a patient", patient_options)
    
    # Extract patient ID from selection
    patient_id = selected_patient.split("ID: ")[1].rstrip(")")
    st.session_state.current_patient_id = patient_id
    
    # Load patient data
    patient_data = get_patient(patient_id)
    
    if patient_data:
        st.info(f"Screening for: {patient_data.get('name', '')}, {patient_data.get('age', '')} years old")
        
        # Select screening tool
        st.sidebar.subheader("Select Screening Tool")
        screening_tool = st.sidebar.radio("Tool", ["SRQ-20", "SRQ-29 WHO", "DASS-42"])
        st.session_state.current_screening_tool = screening_tool
        
        # Display summary of risk assessment from listening module
        with st.expander("Risk Assessment Summary"):
            suicide_risk = patient_data.get('suicide_risk', 'Not assessed')
            harm_risk = patient_data.get('harm_risk', 'Not assessed')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Suicide Risk", suicide_risk)
            with col2:
                st.metric("Risk of Harm to Others", harm_risk)
            
            high_risk = patient_data.get('high_risk', False)
            if high_risk:
                st.warning("⚠️ HIGH RISK ALERT: This patient has been flagged as high risk during the listening assessment.")
        
        # Display selected screening tool
        if screening_tool == "SRQ-20":
            st.subheader("Self-Reporting Questionnaire (SRQ-20)")
            st.write("The SRQ-20 is a screening tool designed to identify mental health problems in primary care settings.")
            
            # Get SRQ-20 questions
            srq_questions = get_srq20_questions()
            
            # Get previous answers if they exist
            previous_answers = patient_data.get('srq_answers', {})
            
            with st.form("srq_form"):
                st.write("In the past 30 days:")
                
                srq_answers = {}
                for i, question in enumerate(srq_questions, 1):
                    key = f"srq_{i}"
                    # Use previous answer as default if available
                    default = previous_answers.get(key, False)
                    srq_answers[key] = st.checkbox(f"{i}. {question}", value=default)
                
                submitted = st.form_submit_button("Calculate SRQ-20 Score")
                
                if submitted:
                    # Calculate score
                    score = sum(1 for key, value in srq_answers.items() if value)
                    
                    # Prepare screening data
                    screening_data = {
                        'srq20_score': score,
                        'srq_answers': srq_answers,
                        'srq20_complete': True,
                        'referral_needed': score >= 8  # Threshold for referral
                    }
                    
                    # Update patient data
                    update_patient_screening_data(screening_data)
                    
                    # Display results
                    st.success(f"SRQ-20 Score: {score}/20")
                    
                    if score >= 11:
                        st.error("Severe mental distress indicated. Referral to a mental health professional is strongly recommended.")
                    elif score >= 8:
                        st.warning("Moderate mental distress indicated. Consider referral to a mental health professional.")
                    elif score >= 5:
                        st.info("Mild mental distress indicated. Continue monitoring and provide basic support.")
                    else:
                        st.info("No significant mental distress indicated.")
                    
                    # Show referral button
                    if score >= 8:
                        if st.button("Proceed to Referral"):
                            st.switch_page("pages/4_Referral_System.py")
        
        elif screening_tool == "SRQ-29 WHO":
            st.subheader("Self-Reporting Questionnaire (SRQ-29 WHO)")
            st.write("The SRQ-29 WHO extends the SRQ-20 with additional questions about psychotic symptoms, epileptic seizures, and alcohol use.")
            
            # Get SRQ-29 questions
            srq_questions = get_srq29_questions()
            
            # Get previous answers if they exist
            previous_answers = patient_data.get('srq_answers', {})
            
            with st.form("srq29_form"):
                st.write("In the past 30 days:")
                
                # Create tabs for different sections
                tab1, tab2, tab3, tab4 = st.tabs(["Anxiety & Depression (1-20)", "Psychotic Symptoms (21-24)", 
                                                 "Epilepsy (25)", "Alcohol Use (26-29)"])
                
                srq_answers = {}
                
                with tab1:
                    st.subheader("Anxiety & Depression Symptoms")
                    # First 20 questions (SRQ-20 part)
                    for i, question in enumerate(srq_questions[:20], 1):
                        key = f"srq_{i}"
                        # Use previous answer as default if available
                        default = previous_answers.get(key, False)
                        srq_answers[key] = st.checkbox(f"{i}. {question}", value=default)
                
                with tab2:
                    st.subheader("Psychotic Symptoms")
                    # Questions 21-24 (Psychotic symptoms)
                    for i, question in enumerate(srq_questions[20:24], 21):
                        key = f"srq_{i}"
                        # Use previous answer as default if available
                        default = previous_answers.get(key, False)
                        srq_answers[key] = st.checkbox(f"{i}. {question}", value=default)
                
                with tab3:
                    st.subheader("Epileptic Seizures")
                    # Question 25 (Epileptic seizures)
                    key = "srq_25"
                    default = previous_answers.get(key, False)
                    srq_answers[key] = st.checkbox(f"25. {srq_questions[24]}", value=default)
                
                with tab4:
                    st.subheader("Alcohol Use")
                    # Questions 26-29 (Alcohol use)
                    for i, question in enumerate(srq_questions[25:], 26):
                        key = f"srq_{i}"
                        # Use previous answer as default if available
                        default = previous_answers.get(key, False)
                        srq_answers[key] = st.checkbox(f"{i}. {question}", value=default)
                
                submitted = st.form_submit_button("Calculate SRQ-29 Score")
                
                if submitted:
                    # Calculate scores
                    total_score = calculate_srq29_score(srq_answers)
                    subscale_scores = get_srq29_subscale_scores(srq_answers)
                    
                    # Prepare screening data
                    screening_data = {
                        'srq29_score': total_score,
                        'srq29_anxiety_depression': subscale_scores['anxiety_depression'],
                        'srq29_psychotic': subscale_scores['psychotic'],
                        'srq29_epileptic': subscale_scores['epileptic'],
                        'srq29_alcohol': subscale_scores['alcohol'],
                        'srq_answers': srq_answers,
                        'srq29_complete': True,
                        'referral_needed': total_score >= 10 or subscale_scores['psychotic'] >= 1 or 
                                         subscale_scores['epileptic'] >= 1 or subscale_scores['alcohol'] >= 2
                    }
                    
                    # Update patient data
                    update_patient_screening_data(screening_data)
                    
                    # Display results
                    st.success(f"SRQ-29 Total Score: {total_score}/29")
                    
                    # Display subscale scores
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        anxiety_depression_score = subscale_scores['anxiety_depression']
                        st.metric("Anxiety & Depression", f"{anxiety_depression_score}/20")
                        if anxiety_depression_score >= 11:
                            st.error("Severe")
                        elif anxiety_depression_score >= 8:
                            st.warning("Moderate")
                        elif anxiety_depression_score >= 5:
                            st.info("Mild")
                    
                    with col2:
                        psychotic_score = subscale_scores['psychotic']
                        st.metric("Psychotic Symptoms", f"{psychotic_score}/4")
                        if psychotic_score >= 1:
                            st.error("Requires specialized assessment")
                    
                    with col3:
                        epileptic_score = subscale_scores['epileptic']
                        st.metric("Epileptic Seizures", f"{epileptic_score}/1")
                        if epileptic_score == 1:
                            st.error("Requires medical assessment")
                    
                    with col4:
                        alcohol_score = subscale_scores['alcohol']
                        st.metric("Alcohol Problems", f"{alcohol_score}/4")
                        if alcohol_score >= 2:
                            st.error("Indicates alcohol issues")
                        elif alcohol_score == 1:
                            st.warning("Possible alcohol issues")
                    
                    # Create visualization for subscale scores
                    data = {
                        'Category': ['Anxiety & Depression', 'Psychotic', 'Epileptic', 'Alcohol'],
                        'Score': [
                            subscale_scores['anxiety_depression'],
                            subscale_scores['psychotic'],
                            subscale_scores['epileptic'],
                            subscale_scores['alcohol']
                        ],
                        'Max Score': [20, 4, 1, 4]  # Maximum possible scores for each category
                    }
                    
                    # Calculate percentage of maximum for better visualization
                    data['Percentage'] = [
                        (data['Score'][i] / data['Max Score'][i]) * 100 if data['Max Score'][i] > 0 else 0
                        for i in range(len(data['Score']))
                    ]
                    
                    df = pd.DataFrame(data)
                    
                    fig = px.bar(df, x='Category', y='Percentage', color='Category',
                                text=[f"{s}/{m}" for s, m in zip(data['Score'], data['Max Score'])],
                                title="SRQ-29 WHO Subscale Scores")
                    fig.update_layout(yaxis_title="Percentage of Maximum Score")
                    st.plotly_chart(fig)
                    
                    # Determine if referral is needed
                    referral_needed = (
                        subscale_scores['anxiety_depression'] >= 8 or 
                        subscale_scores['psychotic'] >= 1 or 
                        subscale_scores['epileptic'] == 1 or 
                        subscale_scores['alcohol'] >= 2
                    )
                    
                    if referral_needed:
                        st.warning("Based on the SRQ-29 results, this patient needs referral to appropriate healthcare professionals.")
                        
                        # Provide specific referral guidance
                        if subscale_scores['anxiety_depression'] >= 8:
                            st.info("⚕️ Anxiety & Depression: Refer to mental health professional")
                        
                        if subscale_scores['psychotic'] >= 1:
                            st.info("⚕️ Psychotic Symptoms: Refer to psychiatrist for specialized assessment")
                        
                        if subscale_scores['epileptic'] == 1:
                            st.info("⚕️ Epileptic Seizures: Refer to neurologist or general physician")
                        
                        if subscale_scores['alcohol'] >= 2:
                            st.info("⚕️ Alcohol Issues: Refer to addiction specialist or counselor")
                        
                        if st.button("Proceed to Referral"):
                            st.switch_page("pages/4_Referral_System.py")
                    else:
                        st.info("Based on the SRQ-29 results, this patient may not require immediate specialist referral but should be monitored.")
                        if st.button("Continue to Referral System"):
                            st.switch_page("pages/4_Referral_System.py")
        
        elif screening_tool == "DASS-42":
            st.subheader("Depression, Anxiety and Stress Scale (DASS-42)")
            st.write("The DASS-42 is a set of three self-report scales designed to measure the emotional states of depression, anxiety and stress.")
            
            # Get DASS-42 questions
            dass_questions = get_dass42_questions()
            
            # Get previous answers if they exist
            previous_answers = patient_data.get('dass_answers', {})
            
            with st.form("dass_form"):
                st.write("Please rate how much each statement applied to you over the past week:")
                
                dass_answers = {}
                for i, (category, question) in enumerate(dass_questions, 1):
                    key = f"dass_{i}"
                    st.write(f"**{i}. {question}**")
                    # Use previous answer as default if available
                    default_idx = previous_answers.get(key, 0)
                    
                    options = [
                        "0 - Did not apply to me at all",
                        "1 - Applied to me to some degree",
                        "2 - Applied to me to a considerable degree",
                        "3 - Applied to me very much"
                    ]
                    
                    dass_answers[key] = st.selectbox(
                        f"Question {i}",
                        options=options,
                        index=default_idx,
                        label_visibility="collapsed"
                    )
                    
                    # Convert string selection to numeric value
                    dass_answers[key] = int(dass_answers[key].split(" - ")[0])
                
                submitted = st.form_submit_button("Calculate DASS-42 Scores")
                
                if submitted:
                    # Calculate scores
                    depression_score, anxiety_score, stress_score = calculate_dass42_scores(dass_answers)
                    
                    # Determine severity levels
                    depression_severity = "Normal"
                    if depression_score >= 28:
                        depression_severity = "Extremely Severe"
                    elif depression_score >= 21:
                        depression_severity = "Severe"
                    elif depression_score >= 14:
                        depression_severity = "Moderate"
                    elif depression_score >= 10:
                        depression_severity = "Mild"
                    
                    anxiety_severity = "Normal"
                    if anxiety_score >= 20:
                        anxiety_severity = "Extremely Severe"
                    elif anxiety_score >= 15:
                        anxiety_severity = "Severe"
                    elif anxiety_score >= 10:
                        anxiety_severity = "Moderate"
                    elif anxiety_score >= 8:
                        anxiety_severity = "Mild"
                    
                    stress_severity = "Normal"
                    if stress_score >= 34:
                        stress_severity = "Extremely Severe"
                    elif stress_score >= 26:
                        stress_severity = "Severe"
                    elif stress_score >= 19:
                        stress_severity = "Moderate"
                    elif stress_score >= 15:
                        stress_severity = "Mild"
                    
                    # Referral needed if any category is moderate or above
                    referral_needed = any(severity in ["Moderate", "Severe", "Extremely Severe"] 
                                        for severity in [depression_severity, anxiety_severity, stress_severity])
                    
                    # Prepare screening data
                    screening_data = {
                        'dass_depression_score': depression_score,
                        'dass_anxiety_score': anxiety_score,
                        'dass_stress_score': stress_score,
                        'dass_depression_severity': depression_severity,
                        'dass_anxiety_severity': anxiety_severity,
                        'dass_stress_severity': stress_severity,
                        'dass_answers': dass_answers,
                        'dass_complete': True,
                        'referral_needed': referral_needed
                    }
                    
                    # Update patient data
                    update_patient_screening_data(screening_data)
                    
                    # Display results
                    st.success("DASS-42 Assessment Complete")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Depression", f"{depression_score} - {depression_severity}")
                    with col2:
                        st.metric("Anxiety", f"{anxiety_score} - {anxiety_severity}")
                    with col3:
                        st.metric("Stress", f"{stress_score} - {stress_severity}")
                    
                    # Create a bar chart for visualization
                    data = {
                        'Category': ['Depression', 'Anxiety', 'Stress'],
                        'Score': [depression_score, anxiety_score, stress_score]
                    }
                    df = pd.DataFrame(data)
                    
                    fig = px.bar(df, x='Category', y='Score', color='Category',
                                text_auto=True,
                                title="DASS-42 Scores")
                    st.plotly_chart(fig)
                    
                    if referral_needed:
                        st.warning("Based on the DASS-42 results, this patient may benefit from professional mental health services.")
                        if st.button("Proceed to Referral"):
                            st.switch_page("pages/4_Referral_System.py")
                    else:
                        st.info("Based on the DASS-42 results, this patient does not require immediate professional intervention but should continue to be monitored.")
                        if st.button("Continue to Referral System"):
                            st.switch_page("pages/4_Referral_System.py")

if __name__ == "__main__":
    main()
