import streamlit as st
import pandas as pd
import json
from utils.db_connector import get_db_connection, test_database_connection

st.set_page_config(
    page_title="Psychiatrist Management - PFA Counseling",
    page_icon="👩‍⚕️",
    layout="wide"
)

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

def save_psychiatrist(psychiatrist_data, psychiatrist_id=None):
    """Save or update a psychiatrist in the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Prepare JSON fields
                contact_info = json.dumps(psychiatrist_data.get('contact_info', {}))
                availability = json.dumps(psychiatrist_data.get('availability', {}))
                
                if psychiatrist_id:  # Update existing
                    cur.execute("""
                        UPDATE psychiatrists 
                        SET name = %s, specialization = %s, qualifications = %s,
                            hospital = %s, contact_info = %s, availability = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        psychiatrist_data['name'],
                        psychiatrist_data['specialization'],
                        psychiatrist_data['qualifications'],
                        psychiatrist_data['hospital'],
                        contact_info,
                        availability,
                        psychiatrist_id
                    ))
                else:  # Insert new
                    cur.execute("""
                        INSERT INTO psychiatrists 
                        (name, specialization, qualifications, hospital, contact_info, availability)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        psychiatrist_data['name'],
                        psychiatrist_data['specialization'],
                        psychiatrist_data['qualifications'],
                        psychiatrist_data['hospital'],
                        contact_info,
                        availability
                    ))
                
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            st.error(f"Error saving psychiatrist: {e}")
        finally:
            conn.close()
    return None

def delete_psychiatrist(psychiatrist_id):
    """Delete a psychiatrist from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # First check if the psychiatrist is referenced in any referrals
                cur.execute("SELECT COUNT(*) FROM referrals WHERE psychiatrist_id = %s", (psychiatrist_id,))
                count = cur.fetchone()[0]
                
                if count > 0:
                    return False, f"Cannot delete psychiatrist because they are referenced in {count} referrals"
                
                # If no referrals, proceed with deletion
                cur.execute("DELETE FROM psychiatrists WHERE id = %s", (psychiatrist_id,))
                conn.commit()
                return True, "Psychiatrist deleted successfully"
        except Exception as e:
            st.error(f"Error deleting psychiatrist: {e}")
            return False, f"Error: {e}"
        finally:
            conn.close()
    return False, "Database connection failed"

def main():
    st.title("Psychiatrist Management")
    
    # Check database connection
    connection_status, _ = test_database_connection()
    if not connection_status:
        st.error("Database connection failed. Please check your database settings.")
        return
    
    # Sidebar for navigation
    st.sidebar.title("Actions")
    action = st.sidebar.radio("Choose an action", ["View Psychiatrists", "Add New Psychiatrist", "Edit Psychiatrist", "Delete Psychiatrist"])
    
    if action == "View Psychiatrists":
        st.header("Psychiatrists")
        psychiatrists = get_all_psychiatrists()
        
        if not psychiatrists:
            st.info("No psychiatrists found in the database. Add a new psychiatrist to get started.")
        else:
            # Display as a table
            psychiatrist_table = []
            for p in psychiatrists:
                # Extract email and phone from contact_info if available
                contact_info = p.get('contact_info', {})
                email = contact_info.get('email', '') if isinstance(contact_info, dict) else ''
                phone = contact_info.get('phone', '') if isinstance(contact_info, dict) else ''
                
                psychiatrist_table.append({
                    "ID": p['id'],
                    "Name": p['name'],
                    "Specialization": p['specialization'],
                    "Hospital": p['hospital'],
                    "Email": email,
                    "Phone": phone
                })
            
            df = pd.DataFrame(psychiatrist_table)
            st.dataframe(df, use_container_width=True)
            
            # Display detailed information for a selected psychiatrist
            if psychiatrists:
                psychiatrist_ids = {p['id']: p['name'] for p in psychiatrists}
                selected_id = st.selectbox("Select a psychiatrist to view details", 
                                          options=list(psychiatrist_ids.keys()),
                                          format_func=lambda x: psychiatrist_ids[x])
                
                selected_psychiatrist = next((p for p in psychiatrists if p['id'] == selected_id), None)
                
                if selected_psychiatrist:
                    st.subheader(f"Details for {selected_psychiatrist['name']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Specialization:**", selected_psychiatrist['specialization'])
                        st.write("**Qualifications:**", selected_psychiatrist['qualifications'])
                        st.write("**Hospital:**", selected_psychiatrist['hospital'])
                    
                    with col2:
                        st.write("**Contact Information:**")
                        contact_info = selected_psychiatrist.get('contact_info', {})
                        if isinstance(contact_info, dict):
                            for key, value in contact_info.items():
                                st.write(f"- {key.capitalize()}: {value}")
                        
                        st.write("**Availability:**")
                        availability = selected_psychiatrist.get('availability', {})
                        if isinstance(availability, dict):
                            for day, hours in availability.items():
                                st.write(f"- {day}: {hours}")
    
    elif action == "Add New Psychiatrist":
        st.header("Add New Psychiatrist")
        
        with st.form("add_psychiatrist_form"):
            name = st.text_input("Name")
            specialization = st.text_input("Specialization (e.g., Addiction, Schizophrenia, Child Psychiatry)")
            qualifications = st.text_area("Qualifications and Credentials")
            hospital = st.text_input("Hospital/Clinic")
            
            st.subheader("Contact Information")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            address = st.text_input("Address")
            
            st.subheader("Availability")
            st.markdown("Enter availability for each day (e.g., '9:00 AM - 5:00 PM' or 'Not Available')")
            monday = st.text_input("Monday")
            tuesday = st.text_input("Tuesday")
            wednesday = st.text_input("Wednesday")
            thursday = st.text_input("Thursday")
            friday = st.text_input("Friday")
            saturday = st.text_input("Saturday")
            sunday = st.text_input("Sunday")
            
            submitted = st.form_submit_button("Add Psychiatrist")
            
            if submitted:
                if not name or not specialization or not hospital:
                    st.error("Name, specialization, and hospital are required fields")
                else:
                    # Construct the psychiatrist data
                    psychiatrist_data = {
                        'name': name,
                        'specialization': specialization,
                        'qualifications': qualifications,
                        'hospital': hospital,
                        'contact_info': {
                            'email': email,
                            'phone': phone,
                            'address': address
                        },
                        'availability': {
                            'Monday': monday,
                            'Tuesday': tuesday,
                            'Wednesday': wednesday,
                            'Thursday': thursday,
                            'Friday': friday,
                            'Saturday': saturday,
                            'Sunday': sunday
                        }
                    }
                    
                    result = save_psychiatrist(psychiatrist_data)
                    if result:
                        st.success(f"Psychiatrist {name} added successfully with ID: {result}")
                    else:
                        st.error("Failed to add psychiatrist")
    
    elif action == "Edit Psychiatrist":
        st.header("Edit Psychiatrist")
        
        psychiatrists = get_all_psychiatrists()
        if not psychiatrists:
            st.info("No psychiatrists found in the database.")
            return
        
        # Select psychiatrist to edit
        psychiatrist_ids = {p['id']: p['name'] for p in psychiatrists}
        selected_id = st.selectbox("Select a psychiatrist to edit", 
                                  options=list(psychiatrist_ids.keys()),
                                  format_func=lambda x: psychiatrist_ids[x])
        
        selected_psychiatrist = next((p for p in psychiatrists if p['id'] == selected_id), None)
        
        if selected_psychiatrist:
            with st.form("edit_psychiatrist_form"):
                name = st.text_input("Name", value=selected_psychiatrist['name'])
                specialization = st.text_input("Specialization", value=selected_psychiatrist['specialization'])
                qualifications = st.text_area("Qualifications and Credentials", value=selected_psychiatrist['qualifications'])
                hospital = st.text_input("Hospital/Clinic", value=selected_psychiatrist['hospital'])
                
                contact_info = selected_psychiatrist.get('contact_info', {})
                if not isinstance(contact_info, dict):
                    contact_info = {}
                
                st.subheader("Contact Information")
                email = st.text_input("Email", value=contact_info.get('email', ''))
                phone = st.text_input("Phone", value=contact_info.get('phone', ''))
                address = st.text_input("Address", value=contact_info.get('address', ''))
                
                availability = selected_psychiatrist.get('availability', {})
                if not isinstance(availability, dict):
                    availability = {}
                
                st.subheader("Availability")
                monday = st.text_input("Monday", value=availability.get('Monday', ''))
                tuesday = st.text_input("Tuesday", value=availability.get('Tuesday', ''))
                wednesday = st.text_input("Wednesday", value=availability.get('Wednesday', ''))
                thursday = st.text_input("Thursday", value=availability.get('Thursday', ''))
                friday = st.text_input("Friday", value=availability.get('Friday', ''))
                saturday = st.text_input("Saturday", value=availability.get('Saturday', ''))
                sunday = st.text_input("Sunday", value=availability.get('Sunday', ''))
                
                submitted = st.form_submit_button("Update Psychiatrist")
                
                if submitted:
                    if not name or not specialization or not hospital:
                        st.error("Name, specialization, and hospital are required fields")
                    else:
                        # Construct the updated psychiatrist data
                        psychiatrist_data = {
                            'name': name,
                            'specialization': specialization,
                            'qualifications': qualifications,
                            'hospital': hospital,
                            'contact_info': {
                                'email': email,
                                'phone': phone,
                                'address': address
                            },
                            'availability': {
                                'Monday': monday,
                                'Tuesday': tuesday,
                                'Wednesday': wednesday,
                                'Thursday': thursday,
                                'Friday': friday,
                                'Saturday': saturday,
                                'Sunday': sunday
                            }
                        }
                        
                        result = save_psychiatrist(psychiatrist_data, selected_id)
                        if result:
                            st.success(f"Psychiatrist {name} updated successfully")
                        else:
                            st.error("Failed to update psychiatrist")
    
    elif action == "Delete Psychiatrist":
        st.header("Delete Psychiatrist")
        st.warning("Caution: Deleting a psychiatrist is permanent and cannot be undone.")
        
        psychiatrists = get_all_psychiatrists()
        if not psychiatrists:
            st.info("No psychiatrists found in the database.")
            return
        
        # Select psychiatrist to delete
        psychiatrist_ids = {p['id']: p['name'] for p in psychiatrists}
        selected_id = st.selectbox("Select a psychiatrist to delete", 
                                  options=list(psychiatrist_ids.keys()),
                                  format_func=lambda x: psychiatrist_ids[x])
        
        selected_psychiatrist = next((p for p in psychiatrists if p['id'] == selected_id), None)
        
        if selected_psychiatrist:
            st.write(f"You are about to delete: **{selected_psychiatrist['name']}**")
            
            # Confirmation
            if st.button("Confirm Deletion", type="primary"):
                success, message = delete_psychiatrist(selected_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)

if __name__ == "__main__":
    main()