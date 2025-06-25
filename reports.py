import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_user_tasks, get_task_statistics
from auth import get_current_user_id, get_current_user_name
import io

def create_tasks_dataframe(tasks):
    """Convert tasks to pandas DataFrame."""
    if not tasks:
        return pd.DataFrame()
    
    df = pd.DataFrame(tasks, columns=[
        'ID', 'User_ID', 'Title', 'Description', 'Status', 
        'Priority', 'Category', 'Due_Date', 'Created_At', 'Completed_At'
    ])
    
    # Convert date columns
    df['Created_At'] = pd.to_datetime(df['Created_At'])
    df['Due_Date'] = pd.to_datetime(df['Due_Date'], errors='coerce')
    df['Completed_At'] = pd.to_datetime(df['Completed_At'], errors='coerce')
    
    return df

def generate_task_summary_chart(stats):
    """Generate task summary chart."""
    status_data = {
        'Status': ['To Do', 'In Progress', 'Done', 'Overdue'],
        'Count': [stats['to_do'], stats['in_progress'], stats['done'], stats['overdue']]
    }
    
    df = pd.DataFrame(status_data)
    return df

def generate_productivity_metrics(tasks_df):
    """Calculate productivity metrics."""
    if tasks_df.empty:
        return {}
    
    total_tasks = len(tasks_df)
    completed_tasks = len(tasks_df[tasks_df['Status'] == 'Done'])
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Calculate average completion time for completed tasks
    completed_df = tasks_df[tasks_df['Status'] == 'Done'].copy()
    if not completed_df.empty and completed_df['Completed_At'].notna().any():
        completed_df['completion_time'] = (
            completed_df['Completed_At'] - completed_df['Created_At']
        ).dt.days
        avg_completion_time = completed_df['completion_time'].mean()
    else:
        avg_completion_time = 0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'avg_completion_time': avg_completion_time
    }

def export_to_excel(tasks_df, stats, metrics):
    """Export data to Excel format."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Tasks sheet
        if not tasks_df.empty:
            export_df = tasks_df.copy()
            export_df = export_df.drop(['ID', 'User_ID'], axis=1)
            export_df.to_excel(writer, sheet_name='Tasks', index=False)
        
        # Summary sheet
        summary_data = {
            'Metric': ['Total Tasks', 'To Do', 'In Progress', 'Done', 'Overdue', 
                      'Completion Rate (%)', 'Avg Completion Time (days)'],
            'Value': [stats['total'], stats['to_do'], stats['in_progress'], 
                     stats['done'], stats['overdue'], round(metrics.get('completion_rate', 0), 2),
                     round(metrics.get('avg_completion_time', 0), 2)]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Weekly breakdown
        if not tasks_df.empty:
            weekly_data = create_weekly_breakdown(tasks_df)
            weekly_data.to_excel(writer, sheet_name='Weekly_Breakdown', index=False)
    
    output.seek(0)
    return output

def create_weekly_breakdown(tasks_df):
    """Create weekly task breakdown."""
    if tasks_df.empty:
        return pd.DataFrame()
    
    # Group by week
    tasks_df['Week'] = tasks_df['Created_At'].dt.to_period('W')
    weekly_stats = tasks_df.groupby(['Week', 'Status']).size().reset_index(name='Count')
    weekly_pivot = weekly_stats.pivot(index='Week', columns='Status', values='Count').fillna(0)
    
    return weekly_pivot.reset_index()

def show_date_range_selector():
    """Show date range selector for filtering reports."""
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=30)
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date()
        )
    
    return start_date, end_date

def filter_tasks_by_date(tasks_df, start_date, end_date):
    """Filter tasks by date range."""
    if tasks_df.empty:
        return tasks_df
    
    mask = (
        (tasks_df['Created_At'].dt.date >= start_date) & 
        (tasks_df['Created_At'].dt.date <= end_date)
    )
    return tasks_df[mask]

def reports_page():
    """Main reports page."""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Please login to view reports")
        return
    
    st.title("📊 Task Reports & Analytics")
    
    # Date range selector
    st.subheader("📅 Select Date Range")
    start_date, end_date = show_date_range_selector()
    
    # Get data
    all_tasks = get_user_tasks(user_id)
    tasks_df = create_tasks_dataframe(all_tasks)
    
    # Filter by date range
    filtered_df = filter_tasks_by_date(tasks_df, start_date, end_date)
    
    # Calculate metrics
    stats = get_task_statistics(user_id)
    metrics = generate_productivity_metrics(filtered_df)
    
    st.divider()
    
    # Key Metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", metrics.get('total_tasks', 0))
    with col2:
        st.metric("Completed", metrics.get('completed_tasks', 0))
    with col3:
        st.metric("Completion Rate", f"{metrics.get('completion_rate', 0):.1f}%")
    with col4:
        st.metric("Avg Completion Time", f"{metrics.get('avg_completion_time', 0):.1f} days")
    
    st.divider()
    
    # Charts
    st.subheader("📊 Task Distribution")
    
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_counts = filtered_df['Status'].value_counts()
            st.bar_chart(status_counts)
            st.caption("Tasks by Status")
        
        with col2:
            # Priority distribution
            priority_counts = filtered_df['Priority'].value_counts()
            st.bar_chart(priority_counts)
            st.caption("Tasks by Priority")
        
        # Category breakdown
        if len(filtered_df['Category'].unique()) > 1:
            st.subheader("📂 Tasks by Category")
            category_counts = filtered_df['Category'].value_counts()
            st.bar_chart(category_counts)
    
    else:
        st.info("No tasks found in the selected date range.")
    
    st.divider()
    
    # Export section
    st.subheader("📥 Export Data")
    
    if st.button("📊 Generate Excel Report"):
        if not tasks_df.empty:
            excel_file = export_to_excel(filtered_df, stats, metrics)
            user_name = get_current_user_name()
            filename = f"Task_Report_{user_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            st.download_button(
                label="⬬ Download Excel Report",
                data=excel_file.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("Excel report generated successfully!")
        else:
            st.warning("No data available to export.")
    
    # Raw data table
    if st.checkbox("Show Raw Data"):
        if not filtered_df.empty:
            display_df = filtered_df.drop(['ID', 'User_ID'], axis=1)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No data to display.") 