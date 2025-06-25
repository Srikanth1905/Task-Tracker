import streamlit as st
import bcrypt
import sqlite3
from datetime import datetime
from database import init_db, get_user_by_email, get_user_by_username, create_user

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user():
    """Handle user registration."""
    st.subheader("🔐 Create New Account")
    
    with st.form("register_form"):
        name = st.text_input("Username", help="This will be your login username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")
        
        if submit:
            if not all([name, email, password, confirm_password]):
                st.error("Please fill in all fields")
                return False
                
            if password != confirm_password:
                st.error("Passwords do not match")
                return False
                
            if len(password) < 6:
                st.error("Password must be at least 6 characters long")
                return False
                
            # Check if user already exists (by username or email)
            existing_user_by_username = get_user_by_username(name)
            existing_user_by_email = get_user_by_email(email)
            
            if existing_user_by_username:
                st.error("Username already taken")
                return False
                
            if existing_user_by_email:
                st.error("Email already registered")
                return False
                
            # Create new user
            hashed_password = hash_password(password)
            if create_user(name, email, hashed_password):
                st.success("Account created successfully! Please login with your username.")
                return True
            else:
                st.error("Failed to create account")
                return False

def login_user():
    """Handle user login."""
    st.subheader("🔑 Login to Your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
                return False
                
            user = get_user_by_username(username)
            if user and verify_password(password, user[2]):  # user[2] is hashed_password
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.user_name = user[1]
                st.session_state.user_email = user[3]
                st.success(f"Welcome back, {user[1]}!")
                st.rerun()
                return True
            else:
                st.error("Invalid username or password")
                return False

def logout_user():
    """Handle user logout."""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.success("Logged out successfully!")
    st.rerun()

def check_authentication():
    """Check if user is authenticated."""
    return st.session_state.get('logged_in', False)

def get_current_user_id():
    """Get current user's ID."""
    return st.session_state.get('user_id', None)

def get_current_user_name():
    """Get current user's name."""
    return st.session_state.get('user_name', None)

def show_auth_sidebar():
    """Show authentication options in sidebar."""
    if check_authentication():
        st.sidebar.success(f"Logged in as: {get_current_user_name()}")
        if st.sidebar.button("Logout"):
            logout_user()
    else:
        st.sidebar.info("Please login to access your tasks")

def auth_page():
    """Main authentication page."""
    init_db()
    
    if check_authentication():
        st.success(f"Welcome, {get_current_user_name()}!")
        return True
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login_user()
    
    with tab2:
        register_user()
    
    return False 