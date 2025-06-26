import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_user_tasks, get_task_statistics, get_attendance_data
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

def create_attendance_report_data(user_id: int, start_date: str, end_date: str):
    """Create attendance report data combining attendance and tasks."""
    # Get attendance data
    attendance_data = get_attendance_data(user_id, start_date, end_date)
    
    # Get tasks data for the date range
    tasks_data = get_user_tasks(user_id)
    
    # Create a dictionary to group tasks by date
    tasks_by_date = {}
    for task in tasks_data:
        task_id, user_id_task, title, description, status, priority, category, task_date, created_at, completed_at = task
        if task_date:  # Simplified date filtering
            if task_date not in tasks_by_date:
                tasks_by_date[task_date] = []
            tasks_by_date[task_date].append({
                'title': title,
                'status': status,
                'priority': priority,
                'category': category
            })
    
    # Combine attendance and tasks data
    report_data = []
    
    # Add all tasks to report data
    for task_date, daily_tasks in tasks_by_date.items():
        # Add tasks for this date
        for task in daily_tasks:
            report_data.append({
                'Date': task_date,
                'Task': task['title'],
                'Status': task['status'],
                'Priority': task['priority'],
                'Category': task['category']
            })
    
    # If no tasks found, add a simple message
    if not report_data:
        report_data.append({
            'Date': 'No data',
            'Task': 'No tasks found',
            'Status': '-',
            'Priority': '-',
            'Category': '-'
        })
    
    return report_data

def export_attendance_excel(task_data, attendance_data, user_name: str):
    """Export attendance and task report to Excel format."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Tasks sheet
        if task_data:
            tasks_df = pd.DataFrame(task_data)
            tasks_df.to_excel(writer, sheet_name='Tasks', index=False)
        
        # Attendance sheet
        if attendance_data:
            # Format attendance data for Excel
            attendance_excel_data = []
            for attendance in attendance_data:
                date, login_time, logout_time = attendance
                
                # Format times
                login_formatted = "Not recorded"
                logout_formatted = "Not recorded"
                
                if login_time and login_time.strip():
                    try:
                        login_dt = datetime.fromisoformat(login_time)
                        login_formatted = login_dt.strftime("%H:%M:%S")
                    except:
                        login_formatted = login_time  # Use as-is if parsing fails
                
                if logout_time and logout_time.strip():
                    try:
                        logout_dt = datetime.fromisoformat(logout_time)
                        logout_formatted = logout_dt.strftime("%H:%M:%S")
                    except:
                        logout_formatted = logout_time  # Use as-is if parsing fails
                
                attendance_excel_data.append({
                    'Date': date,
                    'Login Time': login_formatted,
                    'Logout Time': logout_formatted
                })
            
            attendance_df = pd.DataFrame(attendance_excel_data)
            attendance_df.to_excel(writer, sheet_name='Attendance', index=False)
        else:
            # Create empty attendance sheet with headers
            empty_attendance = pd.DataFrame(columns=['Date', 'Login Time', 'Logout Time'])
            empty_attendance.to_excel(writer, sheet_name='Attendance', index=False)
        
        # Summary sheet
        if task_data:
            tasks_df = pd.DataFrame(task_data)
            summary_data = []
            
            # Get unique dates
            unique_dates = tasks_df['Date'].unique()
            
            for date in unique_dates:
                date_data = tasks_df[tasks_df['Date'] == date]
                
                # Count tasks
                tasks_count = len(date_data[date_data['Task'] != 'No tasks found'])
                completed_tasks = len(date_data[date_data['Status'] == 'Completed'])
                in_progress_tasks = len(date_data[date_data['Status'] == 'In Progress'])
                pending_tasks = len(date_data[date_data['Status'] == 'Pending'])
                
                summary_data.append({
                    'Date': date,
                    'Total Tasks': tasks_count,
                    'Pending Tasks': pending_tasks,
                    'In Progress Tasks': in_progress_tasks,
                    'Completed Tasks': completed_tasks,
                    'Completion Rate': f"{(completed_tasks/tasks_count*100):.1f}%" if tasks_count > 0 else "0%"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output

def show_attendance_metrics(report_data):
    """Display attendance and task metrics."""
    if not report_data:
        return
        
    df = pd.DataFrame(report_data)
    
    # Calculate metrics
    total_days = len(df['Date'].unique())
    total_tasks = len(df[df['Task'] != 'No tasks found'])
    pending_tasks = len(df[df['Status'] == 'Pending'])
    in_progress_tasks = len(df[df['Status'] == 'In Progress'])
    completed_tasks = len(df[df['Status'] == 'Completed'])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Days Tracked", total_days)
    with col2:
        st.metric("Total Tasks", total_tasks)
    with col3:
        st.metric("⏳ Pending", pending_tasks)
    with col4:
        st.metric("🔄 In Progress", in_progress_tasks)
    with col5:
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        st.metric("✅ Completed", f"{completed_tasks} ({completion_rate:.1f}%)")

def show_daily_breakdown(report_data):
    """Show daily attendance and task breakdown."""
    if not report_data:
        return
    
    df = pd.DataFrame(report_data)
    
    # Group by date
    for date in df['Date'].unique():
        with st.expander(f"📅 {date}", expanded=False):
            date_data = df[df['Date'] == date]
            
            # Show tasks
            tasks = date_data[date_data['Task'] != 'No tasks found']
            if not tasks.empty:
                st.write("**Tasks:**")
                for _, task in tasks.iterrows():
                    if task['Status'] == 'Completed':
                        status_icon = "✅"
                    elif task['Status'] == 'In Progress':
                        status_icon = "🔄"
                    else:
                        status_icon = "⏳"
                    
                    priority_icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(task['Priority'], "⚪")
                    st.write(f"{status_icon} {priority_icon} **{task['Task']}** ({task['Category']})")
            else:
                st.write("No tasks recorded for this day")

def reports_page():
    """Main reports page."""
    user_id = get_current_user_id()
    if not user_id:
        st.error("Please login to view reports")
        return
    
    st.title("📊 Attendance & Task Reports")
    
    # Date range selector
    st.subheader("📅 Select Date Range")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=7)
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date()
        )
    
    if start_date > end_date:
        st.error("Start date cannot be after end date")
        return
    
    # Generate report data
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()
    report_data = create_attendance_report_data(user_id, start_date_str, end_date_str)
    
    st.divider()
    
    # Show metrics
    st.subheader("📈 Overview")
    show_attendance_metrics(report_data)
    
    st.divider()
    
    # Export section
    st.subheader("📥 Export Report")
    
    if st.button("📊 Generate Excel Report"):
        if report_data:
            from database import get_user_attendance
            
            user_name = get_current_user_name()
            
            # Get attendance data for the same date range
            attendance_data = get_user_attendance(user_id, start_date, end_date)
            
            # Debug: Show what data we're getting
            st.write(f"**Debug Info:**")
            st.write(f"- Task data records: {len(report_data) if report_data else 0}")
            st.write(f"- Attendance data records: {len(attendance_data) if attendance_data else 0}")
            
            if attendance_data:
                st.write("**Sample attendance data:**")
                for i, record in enumerate(attendance_data[:3]):  # Show first 3 records
                    st.write(f"Record {i+1}: {record}")
            else:
                st.warning("⚠️ No attendance data found for the selected date range. Make sure you have added attendance entries in the Attendance page.")
            
            # Export with both task and attendance data
            excel_file = export_attendance_excel(report_data, attendance_data, user_name)
            filename = f"Complete_Report_{user_name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
            
            st.download_button(
                label="⬇️ Download Excel Report",
                data=excel_file.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("Excel report generated successfully!")
        else:
            st.warning("No data available for the selected date range.")
    
    st.divider()
    
    # Daily breakdown
    st.subheader("📋 Daily Breakdown")
    show_daily_breakdown(report_data)
    
    # Raw data table
    if st.checkbox("Show Raw Data Table"):
        if report_data:
            df = pd.DataFrame(report_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data to display for the selected date range.") 
