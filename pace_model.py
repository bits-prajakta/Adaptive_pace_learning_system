from database import get_db_connection
from datetime import datetime
import json

def calculate_quiz_score(accuracy: float, time_taken_sec: float, num_questions: int) -> float:
    """
    Calculates a combined performance score between 0 and 100.
    - Accuracy determines up to 70 points (accuracy * 70).
    - Average time per question determines up to 30 points.
      If avg time is <= 10s, full 30 pts.
      If avg time is >= 90s, 0 pts.
      Otherwise, scales linearly between 10s and 90s.
    """
    accuracy_score = accuracy * 70.0
    
    t_avg = time_taken_sec / max(1, num_questions)
    if t_avg <= 10.0:
        speed_score = 30.0
    elif t_avg >= 90.0:
        speed_score = 0.0
    else:
        # Scale between 10 and 90 seconds
        speed_score = 30.0 * (1.0 - (t_avg - 10.0) / 80.0)
        
    return float(accuracy_score + speed_score)

def get_pace_category(score: float) -> str:
    """Maps a pace score [0, 100] to a learning category."""
    if score < 20.0:
        return "Super Slow"
    elif score < 40.0:
        return "Slow"
    elif score < 60.0:
        return "Medium"
    elif score < 75.0:
        return "Average"
    elif score < 90.0:
        return "Fast"
    else:
        return "Super Fast"

def update_learning_pace(username: str, topic_name: str, score: int, total_questions: int, time_taken_sec: float):
    """
    Calculates the rolling/time-based learning pace for a user on a given topic,
    saves the quiz details in history, logs the interaction, and updates the topic's pace.
    
    Returns:
        tuple: (new_pace_category, new_pace_score, attempt_number)
    """
    accuracy = float(score / total_questions) if total_questions > 0 else 0.0
    new_quiz_score = calculate_quiz_score(accuracy, time_taken_sec, total_questions)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Determine attempt number
        cursor.execute(
            "SELECT COUNT(*) FROM quiz_history WHERE username = ? AND topic_name = ?",
            (username, topic_name)
        )
        attempts_count = cursor.fetchone()[0]
        attempt_number = attempts_count + 1
        
        # 2. Fetch previous pace score
        cursor.execute(
            "SELECT pace_score FROM topics WHERE username = ? AND topic_name = ?",
            (username, topic_name)
        )
        row = cursor.fetchone()
        
        if row is None:
            # First attempt
            new_pace_score = new_quiz_score
        else:
            prev_pace_score = row["pace_score"]
            # Rolling/Time-based update logic:
            # - rolling_alpha = 0.4 (gives 40% weight to current performance)
            # - delta accounts for the direct improvement / decrement
            rolling_alpha = 0.4
            delta = new_quiz_score - prev_pace_score
            new_pace_score = (rolling_alpha * new_quiz_score) + ((1.0 - rolling_alpha) * prev_pace_score) + (0.1 * delta)
            new_pace_score = max(0.0, min(100.0, new_pace_score))
            
        new_pace_category = get_pace_category(new_pace_score)
        now_str = datetime.now().isoformat()
        
        # 3. Save to Quiz History
        cursor.execute("""
            INSERT INTO quiz_history (username, topic_name, score, total_questions, accuracy, time_taken_sec, attempt_number, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, topic_name, score, total_questions, accuracy, time_taken_sec, attempt_number, now_str))
        
        # 4. Save or Update Topics table
        cursor.execute("""
            INSERT INTO topics (username, topic_name, current_pace, pace_score, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username, topic_name) DO UPDATE SET
                current_pace = excluded.current_pace,
                pace_score = excluded.pace_score
        """, (username, topic_name, new_pace_category, new_pace_score, now_str))
        
        # 5. Log Interaction
        detail_json = json.dumps({
            "score": score,
            "total_questions": total_questions,
            "accuracy": accuracy,
            "time_taken_sec": time_taken_sec,
            "quiz_score": new_quiz_score,
            "pace_score": new_pace_score,
            "pace_category": new_pace_category,
            "attempt": attempt_number
        })
        cursor.execute("""
            INSERT INTO interactions (username, topic_name, interaction_type, detail, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (username, topic_name, "quiz_completed", detail_json, now_str))
        
        conn.commit()
        return new_pace_category, new_pace_score, attempt_number
        
    except Exception as e:
        print(f"Error updating learning pace: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_topic_pace(username: str, topic_name: str):
    """Returns (current_pace, pace_score) or (None, None) if not found."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT current_pace, pace_score FROM topics WHERE username = ? AND topic_name = ?",
            (username, topic_name)
        )
        row = cursor.fetchone()
        if row:
            return row["current_pace"], row["pace_score"]
        return None, None
    finally:
        conn.close()

def get_user_topics(username: str):
    """Returns a list of topics being studied by the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT topic_name, current_pace, pace_score FROM topics WHERE username = ? ORDER BY created_at DESC",
            (username,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
