import hashlib
from datetime import datetime
from database import get_db_connection

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def signup_user(username: str, password: str) -> bool:
    """
    Registers a new user in the system.
    Returns True if registration is successful, False if the user already exists.
    """
    username = username.strip().lower()
    if not username or not password:
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False
            
        password_hash = hash_password(password)
        now_str = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now_str)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error signing up user: {e}")
        return False
    finally:
        conn.close()

def login_user(username: str, password: str) -> bool:
    """
    Checks username and password credentials.
    Returns True if correct, False otherwise.
    """
    username = username.strip().lower()
    if not username or not password:
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return False
            
        stored_hash = row["password_hash"]
        provided_hash = hash_password(password)
        return stored_hash == provided_hash
    except Exception as e:
        print(f"Error logging in user: {e}")
        return False
    finally:
        conn.close()
