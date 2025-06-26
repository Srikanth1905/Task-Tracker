import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Optional

DATABASE_PATH = "data/app.db"

def ensure_data_directory():
    """Ensure the data directory exists."""
    os.makedirs("data", exist_ok=True)

def get_connection():
    """Get database connection."""
    ensure_data_directory()
    return sqlite3.connect(DATABASE_PATH)

def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if tasks table exists and migrate if needed
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if the table has the old schema
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'due_date' in columns and 'task_date' not in columns:
            # Migrate the table
            print("Migrating tasks table...")
            
            # Create new table with correct schema
            cursor.execute('''
                CREATE TABLE tasks_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'Pending',
                    priority TEXT DEFAULT 'Medium',
                    category TEXT DEFAULT 'General',
                    task_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Copy data from old table, renaming due_date to task_date and updating status
            cursor.execute('''
                INSERT INTO tasks_new (id, user_id, title, description, status, priority, category, task_date, created_at, completed_at)
                SELECT id, user_id, title, description, 
                       CASE 
                           WHEN status = 'To Do' THEN 'Pending'
                           WHEN status = 'In Progress' THEN 'Pending' 
                           WHEN status = 'Done' THEN 'Completed'
                           ELSE status
                       END as status,
                       priority, category, 
                       COALESCE(due_date, date('now')) as task_date, 
                       created_at, completed_at
                FROM tasks
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE tasks')
            cursor.execute('ALTER TABLE tasks_new RENAME TO tasks')
            print("Migration completed!")
    else:
        # Create new tasks table
        cursor.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Pending',
                priority TEXT DEFAULT 'Medium',
                category TEXT DEFAULT 'General',
                task_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    
    # Create attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            login_time TIMESTAMP,
            logout_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )
    ''')
    
    conn.commit()
    conn.close()

# User operations
def create_user(name: str, email: str, hashed_password: str) -> bool:
    """Create a new user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_email(email: str) -> Optional[Tuple]:
    """Get user by email."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, hashed_password, email FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_username(username: str) -> Optional[Tuple]:
    """Get user by username."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, hashed_password, email FROM users WHERE name = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Task operations
def create_task(user_id: int, title: str, description: str = "", task_date: str = None, 
                priority: str = "Medium", category: str = "General") -> bool:
    """Create a new task."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (user_id, title, description, task_date, priority, category)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, task_date, priority, category))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_user_tasks(user_id: int, status_filter: str = None) -> List[Tuple]:
    """Get all tasks for a user, optionally filtered by status."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status_filter:
        cursor.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
            (user_id, status_filter)
        )
    else:
        cursor.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str) -> bool:
    """Update task status."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        completed_at = datetime.now().isoformat() if status == "Done" else None
        
        cursor.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed_at, task_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def update_task(task_id: int, title: str, description: str, task_date: str = None,
                priority: str = "Medium", category: str = "General") -> bool:
    """Update task details."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET title = ?, description = ?, task_date = ?, priority = ?, category = ?
            WHERE id = ?
        ''', (title, description, task_date, priority, category, task_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def delete_task(task_id: int) -> bool:
    """Delete a task."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_task_statistics(user_id: int) -> dict:
    """Get task statistics for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count tasks by status
    cursor.execute('''
        SELECT status, COUNT(*) FROM tasks WHERE user_id = ? GROUP BY status
    ''', (user_id,))
    status_counts = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'pending': status_counts.get('Pending', 0),
        'in_progress': status_counts.get('In Progress', 0),
        'completed': status_counts.get('Completed', 0),
        'total': sum(status_counts.values())
    }

# Attendance operations
def create_attendance_entry(user_id: int, date: str, login_time: str = None, logout_time: str = None) -> bool:
    """Create or update attendance entry manually."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO attendance (user_id, date, login_time, logout_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, date, login_time, logout_time))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def update_attendance_entry(user_id: int, date: str, login_time: str = None, logout_time: str = None) -> bool:
    """Update existing attendance entry."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if entry exists
        cursor.execute('SELECT * FROM attendance WHERE user_id = ? AND date = ?', (user_id, date))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing entry
            if login_time is not None and logout_time is not None:
                cursor.execute('''
                    UPDATE attendance SET login_time = ?, logout_time = ? 
                    WHERE user_id = ? AND date = ?
                ''', (login_time, logout_time, user_id, date))
            elif login_time is not None:
                cursor.execute('''
                    UPDATE attendance SET login_time = ? 
                    WHERE user_id = ? AND date = ?
                ''', (login_time, user_id, date))
            elif logout_time is not None:
                cursor.execute('''
                    UPDATE attendance SET logout_time = ? 
                    WHERE user_id = ? AND date = ?
                ''', (logout_time, user_id, date))
        else:
            # Create new entry
            cursor.execute('''
                INSERT INTO attendance (user_id, date, login_time, logout_time)
                VALUES (?, ?, ?, ?)
            ''', (user_id, date, login_time, logout_time))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def delete_attendance_entry(user_id: int, date: str) -> bool:
    """Delete attendance entry."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM attendance WHERE user_id = ? AND date = ?', (user_id, date))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_attendance_data(user_id: int, start_date: str = None, end_date: str = None) -> List[Tuple]:
    """Get attendance data for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if start_date and end_date:
        cursor.execute('''
            SELECT date, login_time, logout_time FROM attendance 
            WHERE user_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        ''', (user_id, start_date, end_date))
    else:
        cursor.execute('''
            SELECT date, login_time, logout_time FROM attendance 
            WHERE user_id = ? ORDER BY date DESC
        ''', (user_id,))
    
    attendance = cursor.fetchall()
    conn.close()
    return attendance

def get_user_attendance(user_id: int, start_date, end_date) -> List[Tuple]:
    """Get user attendance data for date range (compatible with date objects)."""
    # Convert date objects to strings if needed
    if hasattr(start_date, 'isoformat'):
        start_date_str = start_date.isoformat()
    else:
        start_date_str = start_date
        
    if hasattr(end_date, 'isoformat'):
        end_date_str = end_date.isoformat()
    else:
        end_date_str = end_date
    
    return get_attendance_data(user_id, start_date_str, end_date_str) 

