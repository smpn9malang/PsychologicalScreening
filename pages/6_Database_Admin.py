import streamlit as st
import os
import json
import pandas as pd
from utils.db_connector import test_database_connection, initialize_database
from utils.database import get_patients, save_patient, DATA_DIR

st.set_page_config(
    page_title="Database Admin - PFA Counseling",
    page_icon="🔧",
    layout="wide"
)

def migrate_file_to_db(patient_id, patient_data):
    """Migrate a patient record from file to database"""
    return save_patient(patient_id, patient_data)

def main():
    st.title("Database Administration")
    
    # Check database connection
    connection_status, message = test_database_connection()
    
    if connection_status:
        st.success(f"✅ Database Connection: {message}")
        
        # Initialize database
        if initialize_database():
            st.success("✅ Database tables and schema initialized successfully")
        else:
            st.error("❌ Failed to initialize database schema")
            
        # Show current database statistics
        st.subheader("Database Statistics")
        
        # Get patients from database
        patients = get_patients()
        
        if patients:
            st.metric("Total Patients", len(patients))
            
            # Show patient list in a dataframe
            patient_data = []
            for p in patients:
                patient_data.append({
                    "ID": p.get('id', ''),
                    "Name": p.get('name', ''),
                    "Age": p.get('age', ''),
                    "Assessment": "✅" if p.get('assessment_complete', False) else "❌",
                    "Listening": "✅" if p.get('listen_complete', False) else "❌", 
                    "Screening": "✅" if p.get('screening_complete', False) else "❌",
                    "Referral": "✅" if p.get('referral_complete', False) else "❌"
                })
            
            if patient_data:
                df = pd.DataFrame(patient_data)
                st.dataframe(df)
    else:
        st.error(f"❌ Database Connection Failed: {message}")
        
        # Show fallback file-based storage info
        st.warning("⚠️ The application is currently using file-based storage as a fallback")
        
        # Check if file-based storage has data
        if os.path.exists(DATA_DIR):
            file_count = len([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
            st.metric("File-based Patient Records", file_count)
            
            if file_count > 0 and st.button("Migrate File Data to Database"):
                st.info("Starting migration of file-based data to database...")
                
                # Try to initialize database
                if initialize_database():
                    migration_success = 0
                    migration_failed = 0
                    
                    for filename in os.listdir(DATA_DIR):
                        if filename.endswith('.json'):
                            file_path = os.path.join(DATA_DIR, filename)
                            try:
                                with open(file_path, 'r') as f:
                                    patient_data = json.load(f)
                                    patient_id = patient_data.get('id')
                                    
                                    if patient_id:
                                        save_patient(patient_id, patient_data)
                                        migration_success += 1
                                    else:
                                        migration_failed += 1
                            except Exception as e:
                                st.error(f"Error migrating {filename}: {e}")
                                migration_failed += 1
                    
                    st.success(f"Migration completed: {migration_success} records migrated successfully, {migration_failed} failed")
                else:
                    st.error("Failed to initialize database for migration")
        else:
            st.info("No file-based patient records found")
    
    # Add database configuration info
    with st.expander("Database Configuration"):
        st.code("""
        Host: pg-smpn9mlg-smpn9mlg-aplikasi-bk.g.aivencloud.com
        Port: 20360
        Database: defaultdb
        SSL Mode: require
        """)
        
        st.info("SSL Certificate is being used for secure connection")
        
        # Allow backup of certificate
        if st.download_button(
            label="Download SSL Certificate",
            data=open("postgresql-cert.pem", "rb").read(),
            file_name="postgresql-cert.pem",
            mime="application/x-pem-file"
        ):
            st.success("Certificate downloaded successfully")

if __name__ == "__main__":
    main()