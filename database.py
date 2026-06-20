import sqlite3
import os
import hashlib
from datetime import datetime

DB_FILE = "learning_system.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and seeds it with mock data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # 2. Topics Table (Track pace & score per topic per user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        topic_name TEXT NOT NULL,
        current_pace TEXT NOT NULL,
        pace_score REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username),
        UNIQUE(username, topic_name)
    )
    """)
    
    # 3. Quiz History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        topic_name TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        accuracy REAL NOT NULL,
        time_taken_sec REAL NOT NULL,
        attempt_number INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    """)
    
    # 4. Interaction Log Table (Videos watched, material read, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        topic_name TEXT NOT NULL,
        interaction_type TEXT NOT NULL, -- 'video_watch', 'read_material', 'quiz_completed'
        detail TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    """)
    
    # 5. Meet Invitations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meet_invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_username TEXT NOT NULL,
        topic_name TEXT NOT NULL,
        pace_level TEXT NOT NULL,
        meet_link TEXT NOT NULL,
        schedule_time TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    
    # Seed mock data if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_mock_data(conn)
        
    conn.close()

def seed_mock_data(conn):
    """Seeds the database with mock students, topics, history, and meet invitations."""
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    
    # Mock users passwords hashed with sha256 (password: 'password123')
    hashed_pw = hashlib.sha256('password123'.encode('utf-8')).hexdigest()
    
    mock_users = [
        ("alice", hashed_pw, now_str),
        ("bob", hashed_pw, now_str),
        ("charlie", hashed_pw, now_str),
        ("diana", hashed_pw, now_str),
        ("ethan", hashed_pw, now_str),
        ("fiona", hashed_pw, now_str),
    ]
    
    cursor.executemany("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", mock_users)
    
    # Mock user topics
    # pace levels: Super Slow, Slow, Medium, Average, Fast, Super Fast
    mock_topics = [
        # Machine Learning learners
        ("alice", "Machine Learning", "Fast", 82.5, now_str),
        ("bob", "Machine Learning", "Slow", 30.0, now_str),
        ("charlie", "Machine Learning", "Medium", 52.0, now_str),
        ("ethan", "Machine Learning", "Average", 68.0, now_str),
        ("fiona", "Machine Learning", "Super Slow", 12.0, now_str),
        # Python Programming learners
        ("alice", "Python Programming", "Super Fast", 94.0, now_str),
        ("diana", "Python Programming", "Average", 65.0, now_str),
        ("bob", "Python Programming", "Slow", 25.0, now_str),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO topics (username, topic_name, current_pace, pace_score, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, mock_topics)
    
    # Mock quiz history for Alice (ML)
    mock_history = [
        ("alice", "Machine Learning", 7, 10, 0.7, 300.0, 1, now_str),
        ("alice", "Machine Learning", 9, 10, 0.9, 210.0, 2, now_str),
        # Charlie (ML)
        ("charlie", "Machine Learning", 5, 10, 0.5, 450.0, 1, now_str),
        ("charlie", "Machine Learning", 6, 10, 0.6, 400.0, 2, now_str),
        # Bob (ML)
        ("bob", "Machine Learning", 3, 10, 0.3, 650.0, 1, now_str),
    ]
    cursor.executemany("""
        INSERT INTO quiz_history (username, topic_name, score, total_questions, accuracy, time_taken_sec, attempt_number, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, mock_history)
    
    # Mock interactions
    mock_interactions = [
        ("alice", "Machine Learning", "video_watch", "Watched 'Neural Networks Demystified' - 15 mins", now_str),
        ("charlie", "Machine Learning", "read_material", "Read article on 'Linear Regression Basics'", now_str),
        ("bob", "Machine Learning", "read_material", "Read foundational PDF on 'Linear Algebra for Beginners'", now_str),
    ]
    cursor.executemany("""
        INSERT INTO interactions (username, topic_name, interaction_type, detail, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, mock_interactions)
    
    # Mock Meet invitations
    mock_meets = [
        ("alice", "Machine Learning", "Fast", "https://meet.google.com/abc-defg-hij", "Tomorrow at 4:00 PM", "Collaborative problem solving on Backpropagation and CNNs.", now_str),
        ("charlie", "Machine Learning", "Medium", "https://meet.google.com/klm-nopq-rst", "Saturday at 11:00 AM", "Let's review bias-variance tradeoff and cross-validation techniques.", now_str),
        ("bob", "Machine Learning", "Slow", "https://meet.google.com/uvw-xyz-abc", "Monday at 6:00 PM", "Going slow over Gradient Descent derivations and calculations.", now_str),
        ("diana", "Python Programming", "Average", "https://meet.google.com/pqr-stuv-wxy", "Friday at 5:00 PM", "Discussing OOP patterns and decorators in Python.", now_str),
    ]
    cursor.executemany("""
        INSERT INTO meet_invitations (host_username, topic_name, pace_level, meet_link, schedule_time, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, mock_meets)
    
    conn.commit()

def get_user_meet_reminders(username: str):
    """
    Finds upcoming meetings scheduled for topics the user is enrolled in.
    Excludes meetings hosted by the user themselves.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Find topics user is studying
        cursor.execute("SELECT topic_name FROM topics WHERE username = ?", (username,))
        topics = [row["topic_name"] for row in cursor.fetchall()]
        if not topics:
            return []
        
        # Query active meet invitations for these topics
        placeholders = ",".join("?" for _ in topics)
        query = f"""
            SELECT host_username, topic_name, pace_level, meet_link, schedule_time, description
            FROM meet_invitations
            WHERE topic_name IN ({placeholders}) AND host_username != ?
            ORDER BY created_at DESC
            LIMIT 5
        """
        cursor.execute(query, topics + [username])
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching reminders: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded.")

