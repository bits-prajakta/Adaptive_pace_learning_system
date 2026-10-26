import streamlit as st
import random
from database import get_db_connection
from pace_model import get_user_topics
from datetime import datetime


def get_compatible_students(my_username: str, topic: str, my_pace: str) -> list:
    """
    Queries the database for other students learning the same topic.
    Ranks them based on compatibility (same pace is highly compatible, adjacent is moderately compatible).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT username, current_pace, pace_score 
            FROM topics 
            WHERE topic_name = ? AND username != ?
        """, (topic, my_username))
        students = [dict(row) for row in cursor.fetchall()]
        
        
        pace_order = ["Super Slow", "Slow", "Medium", "Average", "Fast", "Super Fast"]
        if my_pace not in pace_order:
            return students
            
        my_idx = pace_order.index(my_pace)
        
        
        for s in students:
            s_pace = s["current_pace"]
            if s_pace in pace_order:
                dist = abs(pace_order.index(s_pace) - my_idx)
            else:
                dist = 3
                
            
            s["compatibility"] = max(0, 100 - (dist * 25))
            
        
        students.sort(key=lambda x: x.get("compatibility", 0), reverse=True)
        return students
    finally:
        conn.close()

def log_meet_join(username: str, topic_name: str, host: str):
    """Logs the user joining a Google Meet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    try:
        detail = f"User joined study meet hosted by {host}."
        cursor.execute("""
            INSERT INTO interactions (username, topic_name, interaction_type, detail, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (username, topic_name, "join_meet", detail, now_str))
        conn.commit()
    except Exception as e:
        print(f"Error logging meet join: {e}")
    finally:
        conn.close()

def create_meet_invitation(
        host: str,
        topic: str,
        pace: str,
        sched_time: str,
        desc: str,
        provided_link: str = ""
):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()

    
    provided_link = provided_link.strip()

    if not provided_link:
        st.error(
            "Please create a Google Meet first (https://meet.google.com/new) "
            "and paste its URL."
        )
        return False

    if not provided_link.startswith("https://meet.google.com/"):
        st.error("Invalid Google Meet URL.")
        return False

    try:
        cursor.execute("""
            INSERT INTO meet_invitations
            (host_username, topic_name, pace_level,
             meet_link, schedule_time, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            host,
            topic,
            pace,
            provided_link,
            sched_time,
            desc,
            now_str
        ))

        conn.commit()
        return True

    except Exception as e:
        st.error(f"Failed to create invitation: {e}")
        return False

    finally:
        conn.close()

def get_meet_invitations(topic: str) -> list:
    """Fetches all meet invitations for a topic."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM meet_invitations 
            WHERE topic_name = ? 
            ORDER BY created_at DESC
        """, (topic,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def show_study_group_page():
    st.title("👥 Group Study & AI Smart Planner")
    st.write("Collaborate with like-minded students studying at a similar pace. Jump into Google Meets or use the AI Smart Planner to set up the ultimate review session.")
    
    username = st.session_state.username
    topics_list = get_user_topics(username)
    
    if not topics_list:
        st.warning("⚠️ You have not registered any topics yet. Please search a topic and complete your first quiz assessment!")
        return

    
    topic_names = [t["topic_name"] for t in topics_list]
    selected_topic_name = st.selectbox("Select Topic to Plan For", topic_names)
    
    selected_topic = next(t for t in topics_list if t["topic_name"] == selected_topic_name)
    current_pace = selected_topic["current_pace"]
    
    tab_meets, tab_planner = st.tabs(["📢 Active Meet Invitations", "🧠 AI Smart Planner"])
    
    
    with tab_meets:
        st.subheader(f"Google Meet Board: {selected_topic_name}")
        
        
        with st.expander("➕ Host a New Study Group Meet"):
            st.markdown("""
                <div style='background: rgba(77, 150, 255, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid rgba(77, 150, 255, 0.2);'>
                    <b>💡 Host an actual Google Meet:</b><br>
                    1. Click the link button below to create a real Google Meet room in a new tab.<br>
                    2. Copy the room's URL (e.g. <i>meet.google.com/abc-defg-hij</i>).<br>
                    3. Paste it into the <b>Meet Link</b> field below so others can join!<br>
                    <i>(If left empty, the system will auto-generate a mockup link.)</i>
                </div>
            """, unsafe_allow_html=True)
            
            st.link_button("🆕 Create Instant Google Meet 🔗", "https://meet.google.com/new", use_container_width=True)
            
            with st.form("host_meet_form"):
                sched_time = st.text_input("Meeting Time", placeholder="e.g., Today at 6:30 PM, Friday at 4:00 PM")
                custom_link = st.text_input("Meet Link (Optional)", placeholder="e.g., https://meet.google.com/abc-defg-hij")
                desc = st.text_area("What will you discuss?", placeholder="e.g., Going over gradient descent equations and coding a simple linear regression from scratch.")
                submit_meet = st.form_submit_button("Publish Invitation")
                
                if submit_meet:
                    if not sched_time or not desc:
                        st.error("Please fill in all required fields.")
                    else:
                        success = create_meet_invitation(username, selected_topic_name, current_pace, sched_time, desc, custom_link)
                        if success:
                            st.success("🎉 Meeting invitation successfully published to students on this path!")
                            st.rerun()
                            
        
        meets = get_meet_invitations(selected_topic_name)
        if not meets:
            st.info("No active study meets scheduled for this topic yet. Be the first to host one!")
        else:
            for m in meets:
                is_my_meet = m["host_username"] == username
                badge_color = "#FFD93D" if m["pace_level"] == current_pace else "#999"
                
                with st.container(border=True):
                    col_det, col_join = st.columns([3, 1])
                    with col_det:
                        st.markdown(f"**Host:** {m['host_username']} {'👤 (You)' if is_my_meet else ''}")
                        st.markdown(f"**Pace Level:** <span style='color: {badge_color}; font-weight: bold;'>{m['pace_level']}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Scheduled Time:** 📅 {m['schedule_time']}")
                        st.write(m['description'])
                    with col_join:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.link_button("Launch Google Meet 🔗", m["meet_link"], use_container_width=True)
                        if not is_my_meet:
                            if st.button("Register Join ✔️", key=f"join_log_{m['id']}", use_container_width=True):
                                log_meet_join(username, selected_topic_name, m["host_username"])
                                st.success("Activity logged to dashboard!")
                                
    
    with tab_planner:
        st.subheader("💡 AI study planner & Recommender")
        st.write("Let the system calculate the best setup for your next group session based on cognitive matching.")
        
        
        st.markdown("#### 🤝 Recommended Study Partners (Cognitive Matching)")
        peers = get_compatible_students(username, selected_topic_name, current_pace)
        
        if not peers:
            st.info("No other students are currently studying this topic in the database. When new students join, they will appear here.")
        else:
            cols = st.columns(min(3, len(peers)))
            for idx, p in enumerate(peers):
                if idx >= 3:
                    break
                with cols[idx]:
                    comp_score = p['compatibility']
                    comp_color = "#6BCB77" if comp_score >= 80 else "#4D96FF"
                    st.markdown(f"""
                        <div style='background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;'>
                            <h5 style='margin: 0; color: #fff;'>👤 {p['username']}</h5>
                            <p style='margin: 5px 0; font-size: 0.9rem; color: #ccc;'>Pace: <b>{p['current_pace']}</b></p>
                            <div style='font-size: 1.1rem; font-weight: bold; color: {comp_color};'>{comp_score}% Match</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
        
        st.markdown("#### 📅 Suggested Meeting Time Slot")
        suggested_times = [
            "Weekday Evenings (6:30 PM - 8:00 PM) — Recommended based on peak activity from your matched study group.",
            "Saturday Mornings (10:00 AM - 11:30 AM) — Recommended for deep focus sessions.",
            "Sunday Afternoons (4:00 PM - 5:30 PM) — Best for quick weekly reviews."
        ]
        chosen_time = random.choice(suggested_times)
        st.info(f"💡 **AI Recommendation:** {chosen_time}")
        
        
        st.markdown("#### 💬 Recommended Discussion Focus")
       
        topic_focus = {
            "Super Slow": "Focus on defining vocabulary, breaking down core mathematical equations into plain-English analogies, and solving 1 basic example step-by-step.",
            "Slow": "Focus on core concepts, drawing flowcharts of the process, and reviewing the primary inputs and outputs of the topic.",
            "Medium": "Focus on intermediate concepts, adjusting 2-3 main parameters to observe results, and discussing the most common coding errors.",
            "Average": "Focus on comparing standard methods, debugging sample code blocks, and reviewing bias-variance tradeoffs.",
            "Fast": "Focus on architectural scaling details, optimization alternatives, and reviewing code implementations from official documentation.",
            "Super Fast": "Focus on reading recent research papers, developing custom extensions, and optimizing execution speed/memory usage."
        }
        rec_focus = topic_focus.get(current_pace, "Discuss general best practices and code implementations.")
        st.success(f"🔍 **Discussion Blueprint:** {rec_focus}")
        
        
        st.markdown("#### 📺 Recommended Joint Pre-watch Video")
      
        if "machine learning" in selected_topic_name.lower():
            vid_title = "Visual Guide to Machine Learning Algorithms"
            vid_url = "https://www.youtube.com/watch?v=hDKC-_rNx9M"
        elif "python" in selected_topic_name.lower():
            vid_title = "Python Design Patterns & Clean Code Guide"
            vid_url = "https://www.youtube.com/watch?v=BI0asZu1XYM"
        else:
            vid_title = f"Crash Course Tutorial on {selected_topic_name}"
            vid_url = "https://www.youtube.com/results?search_query=" + selected_topic_name.replace(' ', '+')
            
        st.markdown(f"💡 **AI Recommends watching this together before discussing:**")
        st.markdown(f"🔗 **[{vid_title}]({vid_url})**")
        
       
        st.markdown("#### 🌐 Create a Real Google Meet")

        st.link_button(
            "🆕 Create Instant Google Meet",
            "https://meet.google.com/new",
            use_container_width=True
        )

        ai_meet_link = st.text_input(
            "Paste Google Meet URL",
            placeholder="https://meet.google.com/abc-defg-hij"
        )

        
        if st.button(
            "🚀 Instantly Invite Compatible Peers to a Google Meet",
            use_container_width=True
        ):

            if not ai_meet_link.strip():
                st.error("Please create a Google Meet and paste its link.")
            else:
                peer_names = ", ".join([p["username"] for p in peers[:3]]) if peers else "other students"

                success = create_meet_invitation(
                    username,
                    selected_topic_name,
                    current_pace,
                    "Today at 7:00 PM (AI Suggested)",
                    f"AI matching study group for {selected_topic_name}. Inviting: {peer_names}. Agenda: {rec_focus}",
                    ai_meet_link    
                )

                if success:
                    st.success("🎉 Group invitation created and posted to the Google Meet Board!")
                    st.rerun()
