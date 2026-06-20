import streamlit as st
from database import init_db, get_user_meet_reminders
from views.login import show_login_page
from views.dashboard import show_dashboard_page
from views.quiz import show_quiz_page
from views.materials import show_materials_page
from views.study_group import show_study_group_page

# Set page configuration with title, icon, layout, and state.
st.set_page_config(
    page_title="Antigravity Learn - Adaptive Pace Learning System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema and seeds
init_db()

# Initialize session states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Add global CSS
st.markdown("""
    <style>
    /* Styling elements for a premium dark mode layout */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    div[data-testid="stSidebar"] {
        background-color: #161920;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Ensure high contrast text on ALL buttons */
    button[kind="secondary"] {
        background-color: #1E222D !important;
        color: #FAFAFA !important;
        border: 1px solid #4D96FF !important;
        font-weight: 500 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #2D323F !important;
        border-color: #FFD93D !important;
        color: #FFFFFF !important;
    }
    
    button[kind="primary"] {
        background-color: #4D96FF !important;
        color: #0E1117 !important; /* dark text for high-contrast on light background */
        font-weight: bold !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background-color: #357AE8 !important;
        color: #FFFFFF !important; /* white text on hover */
    }
    
    .stButton>button {
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(77, 150, 255, 0.2);
    }

    /* Style stMetric labels to be highly visible (white/light-grey) */
    div[data-testid="stMetricLabel"] > div {
        color: #CCCCCC !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #FAFAFA !important;
    }
    
    /* Force selectbox, text input, and other widget labels to have visible text */
    label[data-testid="stWidgetLabel"] p {
        color: #FAFAFA !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    
    /* Make tab labels highly visible globally */
    div[data-baseweb="tab"] p {
        color: #CCCCCC !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. AUTHENTICATION ROUTING
if not st.session_state.logged_in:
    show_login_page()
else:
    # 2. APPLICATION SIDEBAR
    st.sidebar.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    st.sidebar.write("Calibrate, learn, and collaborate in real-time.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Navigation")
    
    # Custom sidebar button routing for sleek feel
    pages = {
        "Dashboard": "📊 Progress & Stats",
        "Quiz Arena": "🎯 Search & Quiz",
        "Learning Material": "📚 Study Materials",
        "Group Study": "👥 Group Study & Meets"
    }
    
    for page_key, page_label in pages.items():
        # Highlight active page button
        is_active = st.session_state.current_page == page_key
        button_style = "primary" if is_active else "secondary"
        
        if st.sidebar.button(page_label, key=f"nav_{page_key}", type=button_style, use_container_width=True):
            st.session_state.current_page = page_key
            st.rerun()
            
    st.sidebar.markdown("---")
    
    # LLM Key Config & Status Badge
    st.sidebar.markdown("### ⚙️ LLM Integration")
    user_api_key = st.sidebar.text_input("Gemini API Key", type="password", 
                                          value=st.session_state.get("gemini_key", ""),
                                          placeholder="Enter API Key to enable AI",
                                          help="Input your Gemini API key to query live models. If empty, the app uses built-in templates.")
    
    if user_api_key != st.session_state.get("gemini_key", ""):
        st.session_state.gemini_key = user_api_key
        st.toast("🔑 Gemini API Key updated for this session!")
        st.rerun()

    # Visual badge showing LLM Active vs Template Mode
    if st.session_state.get("gemini_key", "").strip():
        st.sidebar.markdown("""
            <div style='background: rgba(107, 203, 119, 0.15); border: 1px solid #6BCB77; padding: 10px; border-radius: 8px; margin-bottom: 15px;'>
                <span style='color: #6BCB77; font-weight: bold;'>🟢 Gemini AI Active</span><br>
                <span style='font-size: 0.8rem; color: #CCC;'>Generating custom, unique quizzes & study recommendations dynamically for any search topic!</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
            <div style='background: rgba(255, 217, 61, 0.1); border: 1px solid #FFD93D; padding: 10px; border-radius: 8px; margin-bottom: 15px;'>
                <span style='color: #FFD93D; font-weight: bold;'>⚠️ Local Template Mode</span><br>
                <span style='font-size: 0.8rem; color: #CCC;'>Provide a key to generate unique quizzes for custom searches. Otherwise, pre-built templates are used.</span>
            </div>
        """, unsafe_allow_html=True)

    # 3. SIDEBAR STUDY GROUP REMINDERS PANEL
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 Session Reminders")
    reminders = get_user_meet_reminders(st.session_state.username)
    if not reminders:
        st.sidebar.caption("No upcoming study group sessions scheduled.")
    else:
        for r in reminders:
            st.sidebar.markdown(f"""
                <div style='background: rgba(77, 150, 255, 0.1); border-left: 3px solid #4D96FF; padding: 8px; border-radius: 4px; margin-bottom: 8px;'>
                    <b style='font-size:0.85rem; color:#FFF;'>👥 {r['topic_name']} ({r['pace_level']})</b><br>
                    <span style='font-size:0.8rem; color:#CCC;'>Time: {r['schedule_time']}</span><br>
                    <a href='{r['meet_link']}' target='_blank' style='font-size:0.8rem; color:#4D96FF; text-decoration:none;'>Join Meet 🔗</a>
                </div>
            """, unsafe_allow_html=True)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Log Out", key="logout_btn", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.current_page = "Dashboard"
        # Clear other session states
        if "gemini_key" in st.session_state:
            del st.session_state.gemini_key
        st.rerun()

    # 4. PAGE VIEW CONTENT
    current_page = st.session_state.current_page
    
    if current_page == "Dashboard":
        show_dashboard_page()
    elif current_page == "Quiz Arena":
        show_quiz_page()
    elif current_page == "Learning Material":
        show_materials_page()
    elif current_page == "Group Study":
        show_study_group_page()

