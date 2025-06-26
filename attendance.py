import streamlit as st
from datetime import datetime, date, time
from database import (create_attendance_entry, update_attendance_entry, 
                     delete_attendance_entry, get_attendance_data)
from auth import get_current_user_id

def add_attendance_entry():
    """Form to add new attendance entry."""
    st.subheader("➕ Add Attendance Entry")
    
    with st.form("attendance_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            attendance_date = st.date_input("Date", value=datetime.now().date())
            login_time = st.time_input("Login Time", value=time(9, 0))
        
        with col2:
            logout_time = st.time_input("Logout Time", value=time(17, 0))
            
        submit = st.form_submit_button("Add Attendance")
        
        if submit:
            user_id = get_current_user_id()
            date_str = attendance_date.isoformat()
            
            # Convert time to datetime string
            login_datetime = datetime.combine(attendance_date, login_time).isoformat()
            logout_datetime = datetime.combine(attendance_date, logout_time).isoformat()
            
            if create_attendance_entry(user_id, date_str, login_datetime, logout_datetime):
                st.success("Attendance entry added successfully!")
                st.rerun()
            else:
                st.error("Failed to add attendance entry")

def display_attendance_entries():
    """Display existing attendance entries."""
    user_id = get_current_user_id()
    if not user_id:
        return
    
    # Get recent attendance data (last 30 days)
    from datetime import timedelta
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    attendance_data = get_attendance_data(user_id, start_date.isoformat(), end_date.isoformat())
    
    if not attendance_data:
        st.info("No attendance entries found. Add your first entry above!")
        return
    
    st.subheader("📋 Recent Attendance Entries")
    
    for attendance in attendance_data:
        date_str, login_time, logout_time = attendance
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.write(f"📅 **{date_str}**")
            
            with col2:
                login_formatted = ""
                if login_time:
                    login_dt = datetime.fromisoformat(login_time)
                    login_formatted = login_dt.strftime("%H:%M")
                st.write(f"🕐 Login: {login_formatted}")
            
            with col3:
                logout_formatted = ""
                if logout_time:
                    logout_dt = datetime.fromisoformat(logout_time)
                    logout_formatted = logout_dt.strftime("%H:%M")
                st.write(f"🕐 Logout: {logout_formatted}")
            
            with col4:
                if st.button("🗑️", key=f"delete_{date_str}", help="Delete entry"):
                    if delete_attendance_entry(user_id, date_str):
                        st.success("Entry deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry")
            
            st.divider()

def edit_attendance_entry():
    """Form to edit existing attendance entry."""
    st.subheader("✏️ Edit Attendance Entry")
    
    user_id = get_current_user_id()
    if not user_id:
        return
    
    # Get attendance data for selection
    from datetime import timedelta
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    attendance_data = get_attendance_data(user_id, start_date.isoformat(), end_date.isoformat())
    
    if not attendance_data:
        st.info("No attendance entries to edit.")
        return
    
    # Create options for selectbox
    date_options = [attendance[0] for attendance in attendance_data]
    
    with st.form("edit_attendance_form"):
        selected_date = st.selectbox("Select Date to Edit", date_options)
        
        # Find the selected attendance entry
        selected_entry = None
        for attendance in attendance_data:
            if attendance[0] == selected_date:
                selected_entry = attendance
                break
        
        if selected_entry:
            date_str, login_time, logout_time = selected_entry
            
            # Parse existing times
            existing_login = time(9, 0)
            existing_logout = time(17, 0)
            
            if login_time:
                login_dt = datetime.fromisoformat(login_time)
                existing_login = login_dt.time()
            
            if logout_time:
                logout_dt = datetime.fromisoformat(logout_time)
                existing_logout = logout_dt.time()
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_login_time = st.time_input("New Login Time", value=existing_login)
            
            with col2:
                new_logout_time = st.time_input("New Logout Time", value=existing_logout)
            
            update_submit = st.form_submit_button("Update Attendance")
            
            if update_submit:
                # Convert time to datetime string
                date_obj = datetime.fromisoformat(selected_date).date()
                new_login_datetime = datetime.combine(date_obj, new_login_time).isoformat()
                new_logout_datetime = datetime.combine(date_obj, new_logout_time).isoformat()
                
                if update_attendance_entry(user_id, selected_date, new_login_datetime, new_logout_datetime):
                    st.success("Attendance entry updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update attendance entry")

def attendance_page():
    """Main attendance page."""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Please login to manage attendance")
        return
    
    st.title("🕐 Attendance Management")
    
    # Tab layout
    tab1, tab2, tab3 = st.tabs(["Add Entry", "View Entries", "Edit Entry"])
    
    with tab1:
        add_attendance_entry()
    
    with tab2:
        display_attendance_entries()
    
    with tab3:
        edit_attendance_entry() 
