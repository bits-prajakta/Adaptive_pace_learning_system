import streamlit as st
from auth import login_user, signup_user

def show_login_page():
    
    st.markdown("""
        <style>
        .login-container {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 35px;
            border: 2px solid #4D96FF; /* Highlighted thick border for readability */
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            margin-bottom: 25px;
        }
        .main-header {
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 3rem;
            text-align: center;
            margin-bottom: 10px;
        }
        .sub-header {
            text-align: center;
            color: #A5A5A5;
            font-size: 1.1rem;
            margin-bottom: 30px;
        }
        
        /* Enforce high contrast styling for Form Buttons on Login/Signup */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #4D96FF !important;
            color: #0E1117 !important; /* Bold black text on bright blue */
            font-weight: 800 !important;
            border: 2px solid #FFFFFF !important;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            width: 100% !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #357AE8 !important;
            color: #FFFFFF !important;
            border-color: #4D96FF !important;
        }
        
        /* Improve input field visibility */
        input {
            border: 2px solid #555555 !important;
            background-color: #1A1D24 !important;
            color: #FAFAFA !important;
        }
        input:focus {
            border-color: #4D96FF !important;
        }
        
        /* Make form labels highly visible (white/light-grey text) */
        label[data-testid="stWidgetLabel"] p {
            color: #FAFAFA !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        
        /* Make tab labels highly visible */
        div[data-baseweb="tab"] p {
            color: #CCCCCC !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="tab"][aria-selected="true"] p {
            color: #FF6B6B !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>⚡ Adaptive Pace Learning System</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Intelligent Study Companion</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                username_input = st.text_input("Username", placeholder="e.g., alex_learner", key="login_user")
                password_input = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit_login:
                    if not username_input or not password_input:
                        st.error("Please fill in all fields.")
                    else:
                        success = login_user(username_input, password_input)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username_input.strip().lower()
                            st.success("Successfully logged in! Redirecting...")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")
            
        with tab_signup:
            with st.form("signup_form"):
                new_username = st.text_input("Choose Username", placeholder="e.g., student_123", key="signup_user")
                new_password = st.text_input("Choose Password", type="password", placeholder="••••••••", key="signup_pass")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                submit_signup = st.form_submit_button("Register Account", use_container_width=True)
                
                if submit_signup:
                    if not new_username or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        success = signup_user(new_username, new_password)
                        if success:
                            st.success("Account created successfully! You can now Sign In.")
                        else:
                            st.error("Username already exists or system error occurred.")
