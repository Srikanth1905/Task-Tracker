import streamlit as st
from auth import auth_page, check_authentication, show_auth_sidebar, get_current_user_name
from tasks import tasks_page
from reports import reports_page
from database import init_db

# Page configuration
st.set_page_config(
    page_title="Task Tracker Pro",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 2rem;
    }
    
    .user-info {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .task-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Tasks"
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

def show_welcome_dashboard():
    """Display welcome dashboard with quick stats."""
    from database import get_task_statistics
    from auth import get_current_user_id
    
    st.markdown("""
    <div class="user-info">
        <h2>🎉 Welcome to Task Tracker Pro!</h2>
        <p>Your personal productivity companion for managing tasks and tracking progress.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = get_current_user_id()
    if user_id:
        stats = get_task_statistics(user_id)
        
        st.subheader("📊 Quick Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Total Tasks", stats['total'])
        
        with col2:
            st.metric("⏳ To Do", stats['to_do'])
        
        with col3:
            st.metric("🔄 In Progress", stats['in_progress'])
        
        with col4:
            st.metric("✅ Completed", stats['done'])
        
        if stats['overdue'] > 0:
            st.warning(f"⚠️ You have {stats['overdue']} overdue task(s) that need attention!")
        
        # Quick action buttons
        st.subheader("🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("➕ Add New Task", use_container_width=True):
                st.session_state.current_page = "Tasks"
                st.rerun()
        
        with col2:
            if st.button("📋 View All Tasks", use_container_width=True):
                st.session_state.current_page = "Tasks"
                st.rerun()
        
        with col3:
            if st.button("📊 View Reports", use_container_width=True):
                st.session_state.current_page = "Reports"
                st.rerun()

def show_sidebar_navigation():
    """Show navigation in sidebar."""
    st.sidebar.title("📋 Task Tracker Pro")
    
    # Show authentication status
    show_auth_sidebar()
    
    if check_authentication():
        st.sidebar.markdown("---")
        st.sidebar.subheader("📱 Navigation")
        
        # Navigation buttons
        pages = {
            "🏠 Dashboard": "Dashboard",
            "📝 Tasks": "Tasks", 
            "📊 Reports": "Reports"
        }
        
        for page_label, page_key in pages.items():
            if st.sidebar.button(page_label, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.sidebar.markdown("---")
        
        # User info
        user_name = get_current_user_name()
        if user_name:
            st.sidebar.success(f"👤 Hello, {user_name}!")
        
        # App info
        st.sidebar.markdown("---")
        st.sidebar.info("""
        **Task Tracker Pro v1.0**
        
        Features:
        - ✅ Task Management
        - 📊 Analytics & Reports  
        - 📈 Productivity Tracking
        - 📁 Excel Export
        """)
    else:
        st.sidebar.markdown("---")
        st.sidebar.info("""
        **Welcome to Task Tracker Pro!**
        
        Please login or register to:
        - Create and manage tasks
        - Track your productivity
        - Generate reports
        - Export your data
        """)

def main():
    """Main application logic."""
    # Initialize database and session state
    init_db()
    initialize_session_state()
    
    # Show sidebar navigation
    show_sidebar_navigation()
    
    # Main content area
    if not check_authentication():
        # Show authentication page
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        st.title("📋 Task Tracker Pro")
        st.markdown("*Your Personal Productivity Dashboard*")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show features overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📝 Task Management
            - Create, edit, and organize tasks
            - Set priorities and due dates
            - Track progress with status updates
            - Categorize tasks for better organization
            """)
        
        with col2:
            st.markdown("""
            ### 📊 Analytics & Reports
            - View productivity metrics
            - Generate detailed reports
            - Export data to Excel
            - Track completion rates
            """)
        
        with col3:
            st.markdown("""
            ### 🔐 Secure & Personal
            - Secure user authentication
            - Personal task management
            - Data privacy protection
            - Session management
            """)
        
        st.markdown("---")
        
        # Authentication
        auth_page()
        
    else:
        # User is logged in - show main app
        current_page = st.session_state.get('current_page', 'Dashboard')
        
        # Page routing
        if current_page == "Dashboard":
            st.markdown('<div class="main-header">', unsafe_allow_html=True)
            st.title("🏠 Dashboard")
            st.markdown('</div>', unsafe_allow_html=True)
            show_welcome_dashboard()
            
        elif current_page == "Tasks":
            tasks_page()
            
        elif current_page == "Reports":
            reports_page()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>Task Tracker Pro - Built with ❤️ using Streamlit</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 