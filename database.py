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
    
    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'To Do',
            priority TEXT DEFAULT 'Medium',
            category TEXT DEFAULT 'General',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
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
def create_task(user_id: int, title: str, description: str = "", due_date: str = None, 
                priority: str = "Medium", category: str = "General") -> bool:
    """Create a new task."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (user_id, title, description, due_date, priority, category)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, due_date, priority, category))
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

def update_task(task_id: int, title: str, description: str, due_date: str = None,
                priority: str = "Medium", category: str = "General") -> bool:
    """Update task details."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET title = ?, description = ?, due_date = ?, priority = ?, category = ?
            WHERE id = ?
        ''', (title, description, due_date, priority, category, task_id))
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
    
    # Count overdue tasks
    cursor.execute('''
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ? AND due_date < date('now') AND status != 'Done'
    ''', (user_id,))
    overdue_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'to_do': status_counts.get('To Do', 0),
        'in_progress': status_counts.get('In Progress', 0),
        'done': status_counts.get('Done', 0),
        'overdue': overdue_count,
        'total': sum(status_counts.values())
    } 

