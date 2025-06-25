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
            due_date = st.date_input("Due Date", value=None)
            category = st.text_input("Category", value="General")
        
        description = st.text_area("Description")
        submit = st.form_submit_button("Add Task")
        
        if submit:
            if not title:
                st.error("Task title is required")
                return
                
            user_id = get_current_user_id()
            due_date_str = due_date.isoformat() if due_date else None
            
            if create_task(user_id, title, description, due_date_str, priority, category):
                st.success("Task added successfully!")
                st.rerun()
            else:
                st.error("Failed to add task")

def display_task_card(task):
    """Display a task in a card format."""
    task_id, user_id, title, description, status, priority, category, due_date, created_at, completed_at = task
    
    # Color coding for priority and status
    priority_colors = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
    status_colors = {"To Do": "⏳", "In Progress": "🔄", "Done": "✅"}
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{title}**")
            if description:
                st.caption(description)
            
            # Show due date if exists
            if due_date:
                due_date_obj = datetime.fromisoformat(due_date).date()
                if due_date_obj < date.today() and status != "Done":
                    st.markdown(f"🚨 **Overdue:** {due_date}")
                else:
                    st.markdown(f"📅 Due: {due_date}")
        
        with col2:
            st.markdown(f"{priority_colors.get(priority, '⚪')} {priority}")
            st.caption(f"📂 {category}")
        
        with col3:
            # Status selector
            new_status = st.selectbox(
                "Status", 
                ["To Do", "In Progress", "Done"],
                index=["To Do", "In Progress", "Done"].index(status),
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
    task_id, user_id, title, description, status, priority, category, due_date, created_at, completed_at = task
    
    with st.form(f"edit_task_{task_id}"):
        st.subheader("Edit Task")
        
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Title", value=title)
            new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], 
                                    index=["Low", "Medium", "High"].index(priority))
        
        with col2:
            current_due_date = datetime.fromisoformat(due_date).date() if due_date else None
            new_due_date = st.date_input("Due Date", value=current_due_date)
            new_category = st.text_input("Category", value=category)
        
        new_description = st.text_area("Description", value=description or "")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            save = st.form_submit_button("Save Changes")
        with col_cancel:
            cancel = st.form_submit_button("Cancel")
        
        if save:
            new_due_date_str = new_due_date.isoformat() if new_due_date else None
            if update_task(task_id, new_title, new_description, new_due_date_str, 
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
            ["All", "To Do", "In Progress", "Done"],
            key="status_filter"
        )
    
    with col2:
        search_term = st.text_input("Search tasks", key="search_term")
    
    with col3:
        show_overdue = st.checkbox("Show only overdue", key="show_overdue")
    
    return status_filter, search_term, show_overdue

def filter_tasks(tasks, status_filter, search_term, show_overdue):
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
    
    # Filter overdue tasks
    if show_overdue:
        today = date.today()
        filtered_tasks = [
            task for task in filtered_tasks 
            if task[7] and datetime.fromisoformat(task[7]).date() < today and task[4] != "Done"
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
        st.metric("To Do", stats['to_do'])
    with col3:
        st.metric("In Progress", stats['in_progress'])
    with col4:
        st.metric("Completed", stats['done'])
    
    if stats['overdue'] > 0:
        st.warning(f"⚠️ You have {stats['overdue']} overdue task(s)")
    
    st.divider()
    
    # Add new task section
    add_new_task()
    
    st.divider()
    
    # Task filters
    st.subheader("📊 Your Tasks")
    status_filter, search_term, show_overdue = show_task_filters()
    
    # Get and filter tasks
    all_tasks = get_user_tasks(user_id)
    filtered_tasks = filter_tasks(all_tasks, status_filter, search_term, show_overdue)
    
    if not filtered_tasks:
        st.info("No tasks found matching your criteria.")
        return
    
    # Display tasks
    for task in filtered_tasks:
        display_task_card(task) 