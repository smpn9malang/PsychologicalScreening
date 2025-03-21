import os
import json
import datetime
import streamlit as st
from utils.db_connector import get_db_connection, initialize_database

# Fallback to file-based storage if database connection fails
DATA_DIR = "patient_data"

# Initialize database on module load
db_initialized = False

def use_database():
    """Check if we should use the database or file-based storage"""
    # Get or initialize the db_initialized state
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = initialize_database()
    
    return st.session_state.db_initialized

def initialize_db():
    """Initialize the database"""
    if use_database():
        # Database is already initialized
        return True
    else:
        # Fallback to file-based storage
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        return False

def save_patient(patient_id, patient_data):
    """Save patient data to database or file"""
    if use_database():
        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    # Convert Python dict to JSON string
                    patient_data_json = json.dumps(patient_data)
                    
                    # Check if patient already exists
                    cur.execute("SELECT id FROM patients WHERE id = %s", (patient_id,))
                    exists = cur.fetchone()
                    
                    if exists:
                        # Update existing patient
                        cur.execute(
                            "UPDATE patients SET data = %s, updated_at = NOW() WHERE id = %s",
                            (patient_data_json, patient_id)
                        )
                    else:
                        # Insert new patient
                        cur.execute(
                            "INSERT INTO patients (id, data) VALUES (%s, %s)",
                            (patient_id, patient_data_json)
                        )
                    
                    # Commit the transaction
                    conn.commit()
                    conn.close()
                    return patient_id
        except Exception as e:
            st.error(f"Error saving patient to database: {e}")
            # Fall back to file-based storage
    
    # Fallback to file storage if database failed or not available
    initialize_db()
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")
    
    with open(file_path, 'w') as f:
        json.dump(patient_data, f, indent=2)
    
    return patient_id

def get_patient(patient_id):
    """Get patient data from database or file"""
    if use_database():
        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM patients WHERE id = %s", (patient_id,))
                    result = cur.fetchone()
                    conn.close()
                    
                    if result:
                        return json.loads(result[0])
                    return None
        except Exception as e:
            st.error(f"Error retrieving patient from database: {e}")
            # Fall back to file-based storage
    
    # Fallback to file storage if database failed or not available
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    
    return None

def get_patients():
    """Get all patients from the database or file system"""
    if use_database():
        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM patients ORDER BY updated_at DESC")
                    results = cur.fetchall()
                    conn.close()
                    
                    return [json.loads(row[0]) for row in results]
        except Exception as e:
            st.error(f"Error retrieving patients from database: {e}")
            # Fall back to file-based storage
    
    # Fallback to file storage if database failed or not available
    initialize_db()
    
    patients = []
    
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(DATA_DIR, filename)
                
                with open(file_path, 'r') as f:
                    patient_data = json.load(f)
                    patients.append(patient_data)
    
    return patients

def delete_patient(patient_id):
    """Delete a patient from the database or file"""
    if use_database():
        try:
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
                    conn.commit()
                    conn.close()
                    return True
        except Exception as e:
            st.error(f"Error deleting patient from database: {e}")
            # Fall back to file-based storage
    
    # Fallback to file storage if database failed or not available
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    
    return False
