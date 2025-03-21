import os
import json
import datetime

# Directory to store patient data
DATA_DIR = "patient_data"

def initialize_db():
    """Initialize the database directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_patient(patient_id, patient_data):
    """Save patient data to file"""
    initialize_db()
    
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")
    
    with open(file_path, 'w') as f:
        json.dump(patient_data, f, indent=2)
    
    return patient_id

def get_patient(patient_id):
    """Get patient data from file"""
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    
    return None

def get_patients():
    """Get all patients from the database"""
    initialize_db()
    
    patients = []
    
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(DATA_DIR, filename)
            
            with open(file_path, 'r') as f:
                patient_data = json.load(f)
                patients.append(patient_data)
    
    return patients

def delete_patient(patient_id):
    """Delete a patient from the database"""
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    
    return False
