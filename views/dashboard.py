import streamlit as st
import pandas as pd
import json
import plotly.express as px
from database import get_db_connection, get_user_meet_reminders
from pace_model import get_user_topics

def get_quiz_history_data(username: str, topic_name: str) -> pd.DataFrame:
    """Fetches quiz history for plotting progress."""
    conn = get_db_connection()
    try:
        query = """
            SELECT attempt_number, score, total_questions, accuracy, time_taken_sec, timestamp
            FROM quiz_history
            WHERE username = ? AND topic_name = ?
            ORDER BY attempt_number ASC
        """
        df = pd.read_sql_query(query, conn, params=(username, topic_name))
        return df
    finally:
        conn.close()

def get_pace_history_data(username: str, topic_name: str) -> list:
    """Extracts rolling pace score history from the logged interactions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT detail, timestamp 
            FROM interactions 
            WHERE username = ? AND topic_name = ? AND interaction_type = 'quiz_completed'
            ORDER BY timestamp ASC
        """, (username, topic_name))
        
        history = []
        rows = cursor.fetchall()
        for idx, row in enumerate(rows):
            try:
                detail = json.loads(row["detail"])
                history.append({
                    "Attempt": detail.get("attempt", idx + 1),
                    "Pace Score": detail.get("pace_score", 50.0),
                    "Pace Category": detail.get("pace_category", "Medium"),
                    "Timestamp": row["timestamp"]
                })
            except Exception:
                pass
        return history
    finally:
        conn.close()

def get_recent_logs(username: str, limit: int = 5) -> list:
    """Fetches general interaction logs for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT topic_name, interaction_type, detail, timestamp 
            FROM interactions 
            WHERE username = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (username, limit))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def show_dashboard_page():
    st.title("📊 Performance & Growth Dashboard")
    st.write("Track your rolling learning cognitive updates, study speed, and recent activities.")
    
    username = st.session_state.username
    topics_list = get_user_topics(username)
    
    if not topics_list:
        st.warning("⚠️ No data available yet. Please complete a learning quiz to start tracking your progress.")
        if st.button("Start My First Topic Quiz 🎯", use_container_width=True):
            st.session_state.current_page = "Quiz Arena"
            st.rerun()
        return

    
    st.markdown("### 📈 Learning Overview")
    
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT topic_name) FROM topics WHERE username = ?", (username,))
    total_topics = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_history WHERE username = ?", (username,))
    total_quizzes = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(accuracy) FROM quiz_history WHERE username = ?", (username,))
    avg_accuracy = cursor.fetchone()[0] or 0.0
    conn.close()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(f"""
        <div style="
            background-color:#1e293b;
            padding:5px;
            border-radius:5px;
            text-align:center;
        ">
            <h4 style="
                color:white;
                margin-bottom:10px;
            ">
                Active Topics
            </h4>
            <div style="
            background-color:#1e293b;
            padding:5px;
            border-radius:5px;
            text-align:center;
        ">
            <h1 style="
                color:#38bdf8;
            ">
                {total_topics}
            </h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown(f"""
        <div style="
            background-color:#1e293b;
            padding:5px;
            border-radius:5px;
            text-align:center;
        ">
            <h4 style="
                color:white;
                margin-bottom:10px;
            ">
                Quizzes Completed
            </h4>
            <div style="
            background-color:#1e293b;
            padding:5px;
            border-radius:5px;
            text-align:center;
        ">
            <h1 style="
                color:#38bdf8;
            ">
                {total_quizzes}
            </h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown(f"""
        <div style="
            background-color:#1e293b;
            padding:5px;
            border-radius:5px;
            text-align:center;
        ">
            <h4 style="
                color:white;
                margin-bottom:10px;
            ">
                Average Accuracy
            </h4>
            <div style="
            background-color:#1e293b;
            padding:5px;
            border-radius:5px;
            text-align:center;
        ">
            <h1 style="
                color:#38bdf8;
            ">
                {int(avg_accuracy * 100)}%
            </h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

    reminders = get_user_meet_reminders(username)
    if reminders:
        st.markdown("### 🔔 Upcoming Study Group Reminders")
        for r in reminders:
            col_rem_info, col_rem_action = st.columns([5, 1])
            with col_rem_info:
                st.warning(f"📅 **{r['topic_name']} ({r['pace_level']})** study session hosted by **{r['host_username']}** at **{r['schedule_time']}**.")
            with col_rem_action:
                st.link_button("Join Meet 🔗", r["meet_link"], use_container_width=True)
        st.markdown("---")

    
    st.markdown("### 🔍 Topic Deep Dive")
    topic_names = [t["topic_name"] for t in topics_list]
    selected_topic = st.selectbox("Select Topic to Analyze", topic_names)
    
    
    topic_detail = next(t for t in topics_list if t["topic_name"] == selected_topic)
    st.markdown(f"**Current Learning Classification:** `{topic_detail['current_pace']}` (Index: {round(topic_detail['pace_score'], 1)}/100)")
    
    df_quiz = get_quiz_history_data(username, selected_topic)
    pace_history = get_pace_history_data(username, selected_topic)
    
    if df_quiz.empty:
        st.info("No attempts recorded for this topic yet.")
    else:
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("##### 🧠 Rolling ML Pace Score Index")
            if pace_history:
                df_pace = pd.DataFrame(pace_history)
                fig_pace = px.line(
                    df_pace, 
                    x="Attempt", 
                    y="Pace Score", 
                    hover_data=["Pace Category"],
                    markers=True,
                    labels={"Pace Score": "ML Pace index (0-100)", "Attempt": "Quiz Attempt #"},
                    template="plotly_dark"
                )
                fig_pace.update_traces(line_color='#4D96FF', line_width=3)
                fig_pace.update_yaxes(range=[0, 100])
                st.plotly_chart(fig_pace, use_container_width=True)
                
                latest_pace = pace_history[-1]
                score_val = round(latest_pace["Pace Score"], 1)
                cat_val = latest_pace["Pace Category"]
                
                if cat_val in ["Super Fast", "Fast"]:
                    advice = "This shows that you are answering questions rapidly and with high accuracy. You possess a strong understanding of this topic and should study advanced materials and skip basic reviews."
                elif cat_val in ["Medium", "Average"]:
                    advice = "This indicates a balanced learning speed and accuracy. You have a solid baseline comprehension. Continuing with our core articles and videos will keep your growth stable."
                else: 
                    advice = "This shows that you are taking more time to carefully read and answer the quiz questions. This is excellent for deep conceptual absorption! We advise reading foundational guides and watching step-by-step videos before re-quizzing."
                    
                st.markdown(f"""
                    <div style='background-color: rgba(77, 150, 255, 0.1); padding: 12px; border-radius: 8px; border: 1px solid #4D96FF; margin-top: 10px; margin-bottom: 15px;'>
                        <b>💡 Pace Chart Insight:</b> Your learning index is currently at <b>{score_val}/100</b>, classifying you as a <b>{cat_val} Learner</b>. {advice}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No rolling progress logs found.")
                
        with col_g2:
            st.markdown("##### 🎯 Quiz Accuracy Trend")
            df_quiz["Accuracy (%)"] = df_quiz["accuracy"] * 100.0
            fig_acc = px.line(
                df_quiz,
                x="attempt_number",
                y="Accuracy (%)",
                markers=True,
                labels={"Accuracy (%)": "Score Accuracy (%)", "attempt_number": "Quiz Attempt #"},
                template="plotly_dark"
            )
            fig_acc.update_traces(line_color='#6BCB77', line_width=3)
            fig_acc.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_acc, use_container_width=True)
            
            
            latest_acc = df_quiz["Accuracy (%)"].iloc[-1]
            if latest_acc >= 80:
                acc_advice = "Your accuracy is outstanding (80%+)! You have successfully mastered the core elements of this topic."
            elif latest_acc >= 50:
                acc_advice = "Your accuracy is average. Reviewing the recommended articles or study guides will help clarify lingering doubts and boost your score."
            else:
                acc_advice = "Your accuracy is low. We recommend spending time reading foundational summaries and doing group study sessions before attempting this topic's quizzes again."
                
            st.markdown(f"""
                <div style='background-color: rgba(107, 203, 119, 0.1); padding: 12px; border-radius: 8px; border: 1px solid #6BCB77; margin-top: 10px; margin-bottom: 15px;'>
                    <b>💡 Accuracy Insight:</b> Your latest quiz accuracy score is <b>{int(latest_acc)}%</b>. {acc_advice}
                </div>
            """, unsafe_allow_html=True)
            
       
        st.markdown("##### ⏳ Average Speed per Question")
        df_quiz["Seconds Per Question"] = df_quiz["time_taken_sec"] / df_quiz["total_questions"]
        fig_speed = px.bar(
            df_quiz,
            x="attempt_number",
            y="Seconds Per Question",
            labels={"Seconds Per Question": "Avg Secs / Question", "attempt_number": "Quiz Attempt #"},
            template="plotly_dark"
        )
        fig_speed.update_traces(marker_color='#FFD93D')
        st.plotly_chart(fig_speed, use_container_width=True)
        
        
        latest_speed = round(df_quiz["Seconds Per Question"].iloc[-1], 1)
        if latest_speed <= 20:
            speed_advice = "You answer questions very rapidly, showing strong automatic recall of definitions. Just make sure to read complex questions carefully!"
        elif latest_speed <= 50:
            speed_advice = "You are spending a moderate amount of time per question, showing balanced concentration."
        else:
            speed_advice = "You are taking a highly thorough, measured approach to process the text. This is a very steady study habit that minimizes careless errors!"
            
        st.markdown(f"""
            <div style='background-color: rgba(255, 217, 61, 0.1); padding: 12px; border-radius: 8px; border: 1px solid #FFD93D; margin-top: 10px; margin-bottom: 20px;'>
                <b>💡 Speed Insight:</b> In your last quiz, you spent an average of <b>{latest_speed} seconds</b> per question. {speed_advice}
            </div>
        """, unsafe_allow_html=True)
        
    
    st.markdown("---")
    st.markdown("### 📝 Recent Interaction Activity Logs")
    logs = get_recent_logs(username, limit=6)
    
    if not logs:
        st.info("No activities logged yet.")
    else:
        for l in logs:
            action_emoji = {
                "quiz_completed": "🎮",
                "read_material": "📰",
                "video_watch": "🎥",
                "join_meet": "👥"
            }.get(l["interaction_type"], "⚙️")
            
            
            try:
                dt = datetime.fromisoformat(l["timestamp"])
                formatted_time = dt.strftime("%b %d, %Y - %I:%M %p")
            except Exception:
                formatted_time = l["timestamp"]
                
            st.markdown(f"**{action_emoji} [{l['topic_name']}]** {l['detail']} — <span style='font-size:0.85rem; color:#888;'>{formatted_time}</span>", unsafe_allow_html=True)
