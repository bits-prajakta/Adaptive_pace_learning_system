import streamlit as st
from database import get_db_connection
from pace_model import get_user_topics
from quiz_generator import generate_materials
from datetime import datetime

def log_material_interaction(username: str, topic_name: str, mat_type: str, title: str):
    """Logs a user interaction with learning materials to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    try:
        detail_msg = f"User engaged with {mat_type}: '{title}'"
        cursor.execute("""
            INSERT INTO interactions (username, topic_name, interaction_type, detail, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (username, topic_name, mat_type, detail_msg, now_str))
        conn.commit()
        st.toast(f"🎉 Activity logged: Registered {mat_type} progress!")
    except Exception as e:
        st.error(f"Error logging interaction: {e}")
    finally:
        conn.close()

def show_materials_page():
    st.title("📚 Adaptive Learning Center")
    st.write("Access custom-curated articles, tutorials, and videos calibrated to your assessed learning pace.")

    username = st.session_state.username
    topics_list = get_user_topics(username)

    if not topics_list:
        st.warning("⚠️ You haven't taken any quizzes yet! Please search a topic and complete an assessment quiz first.")
        if st.button("Go to Quiz Arena 🎯", use_container_width=True):
            st.session_state.current_page = "Quiz Arena"
            st.rerun()
        return

    
    topic_names = [t["topic_name"] for t in topics_list]
    selected_topic_name = st.selectbox("Select Topic to Study", topic_names)
    
    
    selected_topic = next(t for t in topics_list if t["topic_name"] == selected_topic_name)
    current_pace = selected_topic["current_pace"]
    pace_score = selected_topic["pace_score"]
    
    
    st.markdown(f"""
        <div style='background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;'>
            <span style='font-size: 1.1rem;'>Current Learning Pace: </span>
            <span style='font-size: 1.2rem; font-weight: bold; color: #4D96FF;'>{current_pace} Learner</span>
            <span style='font-size: 0.9rem; color: #aaa; margin-left: 10px;'>(Pace index: {round(pace_score, 1)}/100)</span>
        </div>
    """, unsafe_allow_html=True)
    
    
    api_key_to_use = st.session_state.get("gemini_key", None)
    
    with st.spinner("Generating learning recommendations..."):
        materials = generate_materials(selected_topic_name, current_pace, api_key=api_key_to_use)
        
    if not materials:
        st.error("Failed to load materials.")
        return
        
   
    st.markdown("### 📝 Topic Roadmap")
    st.write(materials["summary"])
    
    col_a, col_v = st.columns(2)
    
   
    with col_a:
        st.markdown("### 📰 Recommended Readings")
        for i, art in enumerate(materials.get("articles", [])):
            with st.container(border=True):
                st.markdown(f"**{art['title']}**")
                st.markdown(f"[Visit Website 🔗]({art['url']})")
                
                
                log_key = f"read_{selected_topic_name}_{i}"
                if st.button("Mark as Read ✓", key=log_key, use_container_width=True):
                    log_material_interaction(username, selected_topic_name, "read_material", art["title"])
                    
   
    with col_v:
        st.markdown("### 🎥 Recommended Video Lectures")
        for i, vid in enumerate(materials.get("videos", [])):
            with st.container(border=True):
                st.markdown(f"**{vid['title']}**")
                st.markdown(f"[Watch on YouTube 📺]({vid['url']})")
                
                log_key = f"watch_{selected_topic_name}_{i}"
                if st.button("Watched Video ✓", key=log_key, use_container_width=True):
                    log_material_interaction(username, selected_topic_name, "video_watch", vid["title"])
                    
    
    st.markdown("---")
    st.subheader("🏁 Ready to verify your progress?")
    st.write("If you feel you have covered these materials and are improving, take an adaptive quiz to update your learning speed and advance your rank.")
    
    if st.button("Take Adaptive Quiz 🎯", use_container_width=True):
       
        st.session_state.quiz_active = False
        st.session_state.quiz_completed = False
        st.session_state.current_page = "Quiz Arena"
        st.rerun()
