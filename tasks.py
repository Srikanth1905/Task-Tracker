import streamlit as st
from datetime import datetime, date
from database import (create_task, get_user_tasks, update_task_status, 
                     update_task, delete_task, get_task_statistics)
from auth import get_current_user_id

def add_new_task():
    """Form to add a new task."""
    st.subheader("➕ Add New Task")
    
    with st.form("new_task_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Task Title*")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
        with col2:
            task_date = st.date_input("Task Date", value=datetime.now().date())
            category = st.text_input("Category", value="General")
        
        description = st.text_area("Description")
        submit = st.form_submit_button("Add Task")
        
        if submit:
            if not title:
                st.error("Task title is required")
                return
                
            user_id = get_current_user_id()
            task_date_str = task_date.isoformat() if task_date else None
            
            if create_task(user_id, title, description, task_date_str, priority, category):
                st.success("Task added successfully!")
                st.rerun()
            else:
                st.error("Failed to add task")

def display_task_card(task):
    """Display a task in a card format."""
    task_id, user_id, title, description, status, priority, category, task_date, created_at, completed_at = task
    
    # Color coding for priority and status
    priority_colors = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
    status_colors = {"Pending": "⏳", "In Progress": "🔄", "Completed": "✅"}
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{title}**")
            if description:
                st.caption(description)
            
            # Show task date
            if task_date:
                st.markdown(f"📅 Date: {task_date}")
        
        with col2:
            st.markdown(f"{priority_colors.get(priority, '⚪')} {priority}")
            st.caption(f"📂 {category}")
            # Show status with icon
            st.markdown(f"{status_colors.get(status, '⚪')} {status}")
        
        with col3:
            # Status selector
            status_options = ["Pending", "In Progress", "Completed"]
            current_index = status_options.index(status) if status in status_options else 0
            
            new_status = st.selectbox(
                "Change Status", 
                status_options,
                index=current_index,
                key=f"status_{task_id}"
            )
            
            if new_status != status:
                if update_task_status(task_id, new_status):
                    st.success("Status updated!")
                    st.rerun()
                else:
                    st.error("Failed to update status")
        
        # Action buttons
        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("Edit", key=f"edit_{task_id}"):
                st.session_state[f"editing_{task_id}"] = True
                st.rerun()
        
        with col_delete:
            if st.button("Delete", key=f"delete_{task_id}"):
                if delete_task(task_id):
                    st.success("Task deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete task")
        
        # Edit form (if editing)
        if st.session_state.get(f"editing_{task_id}", False):
            edit_task_form(task)
        
        st.divider()

def edit_task_form(task):
    """Form to edit an existing task."""
    task_id, user_id, title, description, status, priority, category, task_date, created_at, completed_at = task
    
    with st.form(f"edit_task_{task_id}"):
        st.subheader("Edit Task")
        
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Title", value=title)
            new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], 
                                      index=["Low", "Medium", "High"].index(priority))
        
        with col2:
            current_task_date = datetime.fromisoformat(task_date).date() if task_date else None
            new_task_date = st.date_input("Task Date", value=current_task_date)
            new_category = st.text_input("Category", value=category)
        
        new_description = st.text_area("Description", value=description or "")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            save = st.form_submit_button("Save Changes")
        with col_cancel:
            cancel = st.form_submit_button("Cancel")
        
        if save:
            new_task_date_str = new_task_date.isoformat() if new_task_date else None
            if update_task(task_id, new_title, new_description, new_task_date_str, 
                          new_priority, new_category):
                st.success("Task updated successfully!")
                st.session_state[f"editing_{task_id}"] = False
                st.rerun()
            else:
                st.error("Failed to update task")
        
        if cancel:
            st.session_state[f"editing_{task_id}"] = False
            st.rerun()

def show_task_filters():
    """Show task filtering options."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status", 
            ["All", "Pending", "In Progress", "Completed"],
            key="status_filter"
        )
    
    with col2:
        search_term = st.text_input("Search tasks", key="search_term")
    
    with col3:
        date_filter = st.date_input("Filter by Date", value=None, key="date_filter")
    
    return status_filter, search_term, date_filter

def filter_tasks(tasks, status_filter, search_term, date_filter):
    """Filter tasks based on criteria."""
    filtered_tasks = tasks
    
    # Filter by status
    if status_filter != "All":
        filtered_tasks = [task for task in filtered_tasks if task[4] == status_filter]
    
    # Filter by search term
    if search_term:
        filtered_tasks = [
            task for task in filtered_tasks 
            if search_term.lower() in task[2].lower() or 
               (task[3] and search_term.lower() in task[3].lower())
        ]
    
    # Filter by date
    if date_filter:
        date_str = date_filter.isoformat()
        filtered_tasks = [
            task for task in filtered_tasks 
            if task[7] and task[7] == date_str
        ]
    
    return filtered_tasks

def tasks_page():
    """Main tasks page."""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Please login to view tasks")
        return
    
    st.title("📋 Task Manager")
    
    # Task statistics
    stats = get_task_statistics(user_id)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", stats['total'])
    with col2:
        st.metric("⏳ Pending", stats['pending'])
    with col3:
        st.metric("🔄 In Progress", stats['in_progress'])
    with col4:
        st.metric("✅ Completed", stats['completed'])
    
    st.divider()
    
    # Add new task section
    add_new_task()
    
    st.divider()
    
    # Task filters
    st.subheader("📊 Your Tasks")
    status_filter, search_term, date_filter = show_task_filters()
    
    # Get and filter tasks
    all_tasks = get_user_tasks(user_id)
    filtered_tasks = filter_tasks(all_tasks, status_filter, search_term, date_filter)
    
    if not filtered_tasks:
        st.info("No tasks found matching your criteria.")
        return
    
    # Display tasks
    for task in filtered_tasks:
        display_task_card(task) 
