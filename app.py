import streamlit as st
import pandas as pd
import os
from utils.database import initialize_db, get_patients
from utils.db_connector import test_database_connection, initialize_database

# Page configuration
st.set_page_config(
    page_title="PFA Counseling App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
# First try PostgreSQL database, then fall back to file storage if needed
if 'db_initialized' not in st.session_state:
    connection_ok, _ = test_database_connection()
    if connection_ok:
        st.session_state.db_initialized = initialize_database()
    else:
        st.session_state.db_initialized = False
        initialize_db()  # Initialize file storage as fallback

def main():
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    
    # Main page content
    st.title("Psychological First Aid (PFA) Counseling Application")
    
    st.markdown("""
    ## Welcome to the PFA Counseling Application
    
    This application follows the **Look, Listen, Link** approach for psychological first aid:
    
    1. **Look**: Assess the patient's physical condition and immediate needs
    2. **Listen**: Provide space for patients to share their experiences
    3. **Link**: Connect patients with appropriate healthcare professionals
    
    Use the sidebar navigation or click on the buttons below to access different modules.
    """)
    
    # Display stats
    patients = get_patients()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", len(patients))
    with col2:
        # Count patients that need referral (if referral_needed column exists and is True)
        referrals_needed = sum(1 for p in patients if p.get('referral_needed', False))
        st.metric("Referrals Needed", referrals_needed)
    with col3:
        # Count completed assessments (if assessment_complete column exists and is True)
        completed = sum(1 for p in patients if p.get('assessment_complete', False))
        st.metric("Completed Assessments", completed)
    
    # Quick action buttons
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("New Patient Assessment", use_container_width=True):
            st.switch_page("pages/1_Patient_Assessment.py")
    
    with col2:
        if st.button("View Reports", use_container_width=True):
            st.switch_page("pages/5_Reports.py")
            
    with col3:
        if st.button("Database Admin", use_container_width=True):
            st.switch_page("pages/6_Database_Admin.py")
    
    # Database connection status
    connection_ok, _ = test_database_connection()
    if connection_ok:
        st.success("✅ Using PostgreSQL Database")
    else:
        st.warning("⚠️ Using file-based storage (PostgreSQL connection unavailable)")
    
    # Recent patients
    st.subheader("Recent Patients")
    if patients:
        # Display the 5 most recent patients
        recent_patients = sorted(patients, key=lambda x: x.get('last_updated', ''), reverse=True)[:5]
        
        # Create a dataframe for display
        recent_df = pd.DataFrame([
            {
                "ID": p.get('id', ''),
                "Name": p.get('name', ''),
                "Age": p.get('age', ''),
                "Last Updated": p.get('last_updated', ''),
                "Status": "Complete" if p.get('assessment_complete', False) else "In Progress"
            } for p in recent_patients
        ])
        
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No patients in the database yet. Start by creating a new patient assessment.")

if __name__ == "__main__":
    main()
