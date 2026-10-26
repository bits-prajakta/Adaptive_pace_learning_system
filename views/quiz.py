import streamlit as st
import time
from database import get_db_connection
from pace_model import update_learning_pace, get_user_topic_pace
from quiz_generator import generate_quiz

def show_quiz_page():
    st.markdown("""
        <style>
        .quiz-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .q-header {
            font-size: 1.4rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 20px;
        }
        .game-bar {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        .stat-item {
            font-size: 1.1rem;
            font-weight: bold;
        }
        .option-btn {
            display: block;
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            background: #2D2D2D;
            border: 1px solid #444;
            color: white;
            border-radius: 8px;
            text-align: left;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .option-btn:hover {
            background: #3D3D3D;
            border-color: #666;
        }
        </style>
    """, unsafe_allow_html=True)

    if "quiz_active" not in st.session_state:
        st.session_state.quiz_active = False
    if "quiz_completed" not in st.session_state:
        st.session_state.quiz_completed = False

    username = st.session_state.username

    if not st.session_state.quiz_active and not st.session_state.quiz_completed:
        st.title("🎯 Start a Learning Quiz")
        st.write("Search for a topic you want to learn. If you've studied this topic before, this will generate an **Adaptive Progress Quiz** based on your current pace. If it's a new topic, it will run an **Initial Assessment Quiz**.")

        
        st.sidebar.markdown("### 🔑 Configuration")
        gemini_key = st.sidebar.text_input("Enter Gemini API Key (Optional)", type="password", 
                                           help="Provide your own Gemini Key to generate real-time quizzes. Otherwise, the system uses built-in smart template generators.")
        if gemini_key:
            st.session_state.gemini_key = gemini_key

        topic_search = st.text_input("Search Topic to Learn", placeholder="e.g., Machine Learning, Python Programming, Quantum Computing...")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            start_btn = st.button("🚀 Start Quiz", use_container_width=True)

       
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT topic_name, current_pace FROM topics WHERE username = ?", (username,))
        existing_topics = cursor.fetchall()
        conn.close()

        if existing_topics:
            st.markdown("### 📚 Your Ongoing Topics")
            for t_row in existing_topics:
                t_name = t_row["topic_name"]
                t_pace = t_row["current_pace"]
                
                col_t1, col_t2 = st.columns([3, 1])
                with col_t1:
                    st.info(f"📖 **{t_name}** — Assessed Pace: **{t_pace}**")
                with col_t2:
                    if st.button(f"Retake Quiz: {t_name}", key=f"retake_{t_name}", use_container_width=True):
                        topic_search = t_name
                        start_btn = True

        if start_btn:
            if not topic_search.strip():
                st.error("Please enter or select a topic to search.")
            else:
                topic_name = topic_search.strip()
                st.info(f"Generating quiz for **{topic_name}**... Please wait.")
                
                
                pace_level, _ = get_user_topic_pace(username, topic_name)
                
                if not pace_level:
                    pace_level = "Medium"
                    st.toast(f"New Topic! Starting Initial Assessment Quiz on {topic_name}.")
                else:
                    st.toast(f"Adaptive Re-Quiz loaded for {topic_name} ({pace_level} level).")

                
                api_key_to_use = st.session_state.get("gemini_key", None)
                
                try:
                    questions = generate_quiz(topic_name, pace_level, api_key=api_key_to_use)
                    
                   
                    st.session_state.quiz_topic = topic_name
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_step = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_lives = 3
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_start_time = time.time()
                    st.session_state.quiz_active = True
                    st.session_state.quiz_answered_current = False
                    st.session_state.quiz_selected_ans = None
                    
                    st.rerun()
                except Exception as ex:
                    st.error(f"Failed to generate quiz: {ex}")

    
    elif st.session_state.quiz_active:
        topic = st.session_state.quiz_topic
        questions = st.session_state.quiz_questions
        step = st.session_state.quiz_step
        lives = st.session_state.quiz_lives
        score = st.session_state.quiz_score
        
        if step >= len(questions):
            st.session_state.quiz_active = False
            st.session_state.quiz_completed = True
            st.rerun()
            
        q_data = questions[step]
        
        
        st.markdown(f"## 🎮 Learning Arena: **{topic}**")
        
       
        heart_symbols = "❤️" * max(0, lives) + "🖤" * (3 - max(0, lives))
        elapsed_sec = int(time.time() - st.session_state.quiz_start_time)
        
        st.markdown(f"""
            <div class='game-bar'>
                <span class='stat-item' style='color: #4D96FF;'>📝 Question: {step+1}/10</span>
                <span class='stat-item' style='color: #FF6B6B;'>Health: {heart_symbols}</span>
                <span class='stat-item' style='color: #FFD93D;'>⏳ Time: {elapsed_sec}s</span>
                <span class='stat-item' style='color: #6BCB77;'>🏆 XP: {score * 10}</span>
            </div>
        """, unsafe_allow_html=True)
        
        
        col_pb, col_qt = st.columns([5, 1])
        with col_pb:
            st.progress((step) / 10.0)
        with col_qt:
            if st.button("🚪 Quit", key="quit_quiz_btn", type="secondary", use_container_width=True, help="Abandon this quiz and return to topic search."):
                clean_quiz_state()
                st.toast("🚪 Quiz abandoned. Returned to Search!")
                st.rerun()
        
        
        st.markdown(f"""
            <div class='quiz-card'>
                <div class='q-header'>Q{step+1}: {q_data['question']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        correct_idx = q_data["correct_idx"]
        options = q_data["options"]
        
        
        if not st.session_state.quiz_answered_current:
            
            selected_option = st.radio("Select the correct answer:", options, index=None, key=f"q_{step}_radio")
            submit_ans = st.button("Submit Answer", use_container_width=True)
            
            if submit_ans and selected_option is not None:
                selected_idx = options.index(selected_option)
                st.session_state.quiz_answers[step] = selected_idx
                st.session_state.quiz_answered_current = True
                
                
                if selected_idx == correct_idx:
                    st.session_state.quiz_score += 1
                else:
                    st.session_state.quiz_lives -= 1
                    
                st.rerun()
        else:
            
            selected_idx = st.session_state.quiz_answers[step]
            
            if selected_idx == correct_idx:
                st.success(f"🎉 **Correct!** Excellent job. (+10 XP)")
               
                if step == 9:
                    st.balloons()
            else:
                st.error(f"❌ **Incorrect.** The correct answer was: **{options[correct_idx]}**")
                if lives <= 1:
                    st.warning("⚠️ **Low Health!** Be careful on the next question.")
                    
            st.markdown(f"**Your Answer:** {options[selected_idx]}")
            st.markdown(f"**Correct Answer:** {options[correct_idx]}")
            
            
            next_label = "Finish & Assess" if step == 9 else "Next Question ➡️"
            if st.button(next_label, use_container_width=True):
                st.session_state.quiz_answered_current = False
                st.session_state.quiz_step += 1
                
               
                if st.session_state.quiz_lives <= 0:
                    st.session_state.quiz_active = False
                    st.session_state.quiz_completed = True
                    st.warning("Game Over! Running out of lives, proceeding to results.")
                    
                st.rerun()

    elif st.session_state.quiz_completed:
        topic = st.session_state.quiz_topic
        score = st.session_state.quiz_score
        questions = st.session_state.quiz_questions
        total_questions = len(questions)
        lives = st.session_state.quiz_lives
        
        
        elapsed_sec = float(time.time() - st.session_state.quiz_start_time)
        
        st.balloons()
        st.title("🏆 Quiz Completed!")
        
        st.markdown(f"""
            <div class='quiz-card' style='text-align: center;'>
                <h3 style='color: #FFD93D; margin-bottom: 10px;'>Assessment Complete for {topic}</h3>
                <p style='font-size: 1.1rem; color: #ccc;'>Analyzing performance metrics and updating ML Pace Model...</p>
            </div>
        """, unsafe_allow_html=True)
        
       
        try:
           
            if "assessment_run" not in st.session_state:
                new_pace, new_score, attempt = update_learning_pace(
                    username, topic, score, total_questions, elapsed_sec
                )
                st.session_state.assessment_run = {
                    "pace": new_pace,
                    "score": new_score,
                    "attempt": attempt
                }
            
            assess = st.session_state.assessment_run
            
           
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Score", f"{score} / {total_questions}", f"{int((score/total_questions)*100)}% Accuracy")
            col_m2.metric("Time Taken", f"{int(elapsed_sec)} sec", f"{round(elapsed_sec/total_questions, 1)}s / question")
            col_m3.metric("Evaluated Learning Pace", assess["pace"], f"Score: {round(assess['score'], 1)}/100")
            
            st.markdown(f"""
                <div style='background: rgba(77, 150, 255, 0.1); border-left: 5px solid #4D96FF; padding: 15px; border-radius: 4px; margin: 20px 0;'>
                    <h4>🧠 ML Cognitive Assessment</h4>
                    <p>Based on your <b>accuracy ({int((score/total_questions)*100)}%)</b> and <b>reaction speed ({round(elapsed_sec/total_questions, 1)} seconds per question)</b>, 
                    the system has categorized you as a <b>{assess['pace']} Learner</b> for <b>{topic}</b>. 
                    Your learning pathway, video lectures, reading links, and group meet recommendations have been customized accordingly.</p>
                </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error executing pace model update: {e}")
            
       
        st.write("What would you like to do next?")
        c_a1, c_a2, c_a3 = st.columns(3)
        with c_a1:
            if st.button("📊 View Performance Dashboard", use_container_width=True):
               
                clean_quiz_state()
                st.session_state.current_page = "Dashboard"
                st.rerun()
        with c_a2:
            if st.button("📚 Study Recommended Material", use_container_width=True):
                clean_quiz_state()
                st.session_state.current_page = "Learning Material"
                st.rerun()
        with c_a3:
            if st.button("👥 Join a Study Group Meet", use_container_width=True):
                clean_quiz_state()
                st.session_state.current_page = "Group Study"
                st.rerun()
                
        if st.button("🔄 Start a New Topic Quiz", use_container_width=True):
            clean_quiz_state()
            st.rerun()

def clean_quiz_state():
    """Resets all quiz session states to return to topic search."""
    st.session_state.quiz_active = False
    st.session_state.quiz_completed = False
    if "quiz_topic" in st.session_state:
        del st.session_state.quiz_topic
    if "quiz_questions" in st.session_state:
        del st.session_state.quiz_questions
    if "quiz_step" in st.session_state:
        del st.session_state.quiz_step
    if "quiz_score" in st.session_state:
        del st.session_state.quiz_score
    if "quiz_lives" in st.session_state:
        del st.session_state.quiz_lives
    if "quiz_answers" in st.session_state:
        del st.session_state.quiz_answers
    if "quiz_start_time" in st.session_state:
        del st.session_state.quiz_start_time
    if "quiz_answered_current" in st.session_state:
        del st.session_state.quiz_answered_current
    if "quiz_selected_ans" in st.session_state:
        del st.session_state.quiz_selected_ans
    if "assessment_run" in st.session_state:
        del st.session_state.assessment_run
