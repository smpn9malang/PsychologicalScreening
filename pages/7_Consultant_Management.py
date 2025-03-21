import streamlit as st
import pandas as pd
import json
from utils.db_connector import get_db_connection, test_database_connection

st.set_page_config(
    page_title="Consultant Management - PFA Counseling",
    page_icon="👨‍⚕️",
    layout="wide"
)

def get_all_consultants():
    """Get all mental health consultants from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM consultants ORDER BY name ASC")
                columns = [desc[0] for desc in cur.description]
                result = cur.fetchall()
                
                # Convert to list of dictionaries
                consultants = []
                for row in result:
                    consultant_dict = dict(zip(columns, row))
                    
                    # Parse JSONB fields
                    if 'contact_info' in consultant_dict and consultant_dict['contact_info']:
                        consultant_dict['contact_info'] = json.loads(consultant_dict['contact_info'])
                    if 'availability' in consultant_dict and consultant_dict['availability']:
                        consultant_dict['availability'] = json.loads(consultant_dict['availability'])
                        
                    consultants.append(consultant_dict)
                
                return consultants
        except Exception as e:
            st.error(f"Error retrieving consultants: {e}")
        finally:
            conn.close()
    return []

def save_consultant(consultant_data, consultant_id=None):
    """Save or update a consultant in the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Prepare JSON fields
                contact_info = json.dumps(consultant_data.get('contact_info', {}))
                availability = json.dumps(consultant_data.get('availability', {}))
                
                if consultant_id:  # Update existing
                    cur.execute("""
                        UPDATE consultants 
                        SET name = %s, specialization = %s, qualifications = %s,
                            contact_info = %s, availability = %s
                        WHERE id = %s
                        RETURNING id
                    """, (
                        consultant_data['name'],
                        consultant_data['specialization'],
                        consultant_data['qualifications'],
                        contact_info,
                        availability,
                        consultant_id
                    ))
                else:  # Insert new
                    cur.execute("""
                        INSERT INTO consultants 
                        (name, specialization, qualifications, contact_info, availability)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        consultant_data['name'],
                        consultant_data['specialization'],
                        consultant_data['qualifications'],
                        contact_info,
                        availability
                    ))
                
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
        except Exception as e:
            st.error(f"Error saving consultant: {e}")
        finally:
            conn.close()
    return None

def delete_consultant(consultant_id):
    """Delete a consultant from the database"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # First check if the consultant is referenced in any referrals
                cur.execute("SELECT COUNT(*) FROM referrals WHERE consultant_id = %s", (consultant_id,))
                count = cur.fetchone()[0]
                
                if count > 0:
                    return False, f"Cannot delete consultant because they are referenced in {count} referrals"
                
                # If no referrals, proceed with deletion
                cur.execute("DELETE FROM consultants WHERE id = %s", (consultant_id,))
                conn.commit()
                return True, "Consultant deleted successfully"
        except Exception as e:
            st.error(f"Error deleting consultant: {e}")
            return False, f"Error: {e}"
        finally:
            conn.close()
    return False, "Database connection failed"

def main():
    st.title("Mental Health Consultant Management")
    
    # Check database connection
    connection_status, _ = test_database_connection()
    if not connection_status:
        st.error("Database connection failed. Please check your database settings.")
        return
    
    # Sidebar for navigation
    st.sidebar.title("Actions")
    action = st.sidebar.radio("Choose an action", ["View Consultants", "Add New Consultant", "Edit Consultant", "Delete Consultant"])
    
    if action == "View Consultants":
        st.header("Mental Health Consultants")
        consultants = get_all_consultants()
        
        if not consultants:
            st.info("No consultants found in the database. Add a new consultant to get started.")
        else:
            # Display as a table
            consultant_table = []
            for c in consultants:
                # Extract email and phone from contact_info if available
                contact_info = c.get('contact_info', {})
                email = contact_info.get('email', '') if isinstance(contact_info, dict) else ''
                phone = contact_info.get('phone', '') if isinstance(contact_info, dict) else ''
                
                consultant_table.append({
                    "ID": c['id'],
                    "Name": c['name'],
                    "Specialization": c['specialization'],
                    "Email": email,
                    "Phone": phone
                })
            
            df = pd.DataFrame(consultant_table)
            st.dataframe(df, use_container_width=True)
            
            # Display detailed information for a selected consultant
            if consultants:
                consultant_ids = {c['id']: c['name'] for c in consultants}
                selected_id = st.selectbox("Select a consultant to view details", 
                                          options=list(consultant_ids.keys()),
                                          format_func=lambda x: consultant_ids[x])
                
                selected_consultant = next((c for c in consultants if c['id'] == selected_id), None)
                
                if selected_consultant:
                    st.subheader(f"Details for {selected_consultant['name']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Specialization:**", selected_consultant['specialization'])
                        st.write("**Qualifications:**", selected_consultant['qualifications'])
                    
                    with col2:
                        st.write("**Contact Information:**")
                        contact_info = selected_consultant.get('contact_info', {})
                        if isinstance(contact_info, dict):
                            for key, value in contact_info.items():
                                st.write(f"- {key.capitalize()}: {value}")
                        
                        st.write("**Availability:**")
                        availability = selected_consultant.get('availability', {})
                        if isinstance(availability, dict):
                            for day, hours in availability.items():
                                st.write(f"- {day}: {hours}")
    
    elif action == "Add New Consultant":
        st.header("Add New Mental Health Consultant")
        
        with st.form("add_consultant_form"):
            name = st.text_input("Name")
            specialization = st.text_input("Specialization (e.g., Depression, Anxiety, Family Counseling)")
            qualifications = st.text_area("Qualifications and Credentials")
            
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
            
            submitted = st.form_submit_button("Add Consultant")
            
            if submitted:
                if not name or not specialization:
                    st.error("Name and specialization are required fields")
                else:
                    # Construct the consultant data
                    consultant_data = {
                        'name': name,
                        'specialization': specialization,
                        'qualifications': qualifications,
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
                    
                    result = save_consultant(consultant_data)
                    if result:
                        st.success(f"Consultant {name} added successfully with ID: {result}")
                    else:
                        st.error("Failed to add consultant")
    
    elif action == "Edit Consultant":
        st.header("Edit Mental Health Consultant")
        
        consultants = get_all_consultants()
        if not consultants:
            st.info("No consultants found in the database.")
            return
        
        # Select consultant to edit
        consultant_ids = {c['id']: c['name'] for c in consultants}
        selected_id = st.selectbox("Select a consultant to edit", 
                                  options=list(consultant_ids.keys()),
                                  format_func=lambda x: consultant_ids[x])
        
        selected_consultant = next((c for c in consultants if c['id'] == selected_id), None)
        
        if selected_consultant:
            with st.form("edit_consultant_form"):
                name = st.text_input("Name", value=selected_consultant['name'])
                specialization = st.text_input("Specialization", value=selected_consultant['specialization'])
                qualifications = st.text_area("Qualifications and Credentials", value=selected_consultant['qualifications'])
                
                contact_info = selected_consultant.get('contact_info', {})
                if not isinstance(contact_info, dict):
                    contact_info = {}
                
                st.subheader("Contact Information")
                email = st.text_input("Email", value=contact_info.get('email', ''))
                phone = st.text_input("Phone", value=contact_info.get('phone', ''))
                address = st.text_input("Address", value=contact_info.get('address', ''))
                
                availability = selected_consultant.get('availability', {})
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
                
                submitted = st.form_submit_button("Update Consultant")
                
                if submitted:
                    if not name or not specialization:
                        st.error("Name and specialization are required fields")
                    else:
                        # Construct the updated consultant data
                        consultant_data = {
                            'name': name,
                            'specialization': specialization,
                            'qualifications': qualifications,
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
                        
                        result = save_consultant(consultant_data, selected_id)
                        if result:
                            st.success(f"Consultant {name} updated successfully")
                        else:
                            st.error("Failed to update consultant")
    
    elif action == "Delete Consultant":
        st.header("Delete Mental Health Consultant")
        st.warning("Caution: Deleting a consultant is permanent and cannot be undone.")
        
        consultants = get_all_consultants()
        if not consultants:
            st.info("No consultants found in the database.")
            return
        
        # Select consultant to delete
        consultant_ids = {c['id']: c['name'] for c in consultants}
        selected_id = st.selectbox("Select a consultant to delete", 
                                  options=list(consultant_ids.keys()),
                                  format_func=lambda x: consultant_ids[x])
        
        selected_consultant = next((c for c in consultants if c['id'] == selected_id), None)
        
        if selected_consultant:
            st.write(f"You are about to delete: **{selected_consultant['name']}**")
            
            # Confirmation
            if st.button("Confirm Deletion", type="primary"):
                success, message = delete_consultant(selected_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)

if __name__ == "__main__":
    main()