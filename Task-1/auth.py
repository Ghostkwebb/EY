# auth.py
import streamlit as st

def init_auth():
    """Initializes auth states in session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "is_dev" not in st.session_state:
        st.session_state.is_dev = False

def login_screen():
    """Renders sleek Swiss Neo-Brutalist login card."""
    st.markdown("""
    <style>
        header, [data-testid="stSidebar"] { display: none !important; }
        .stApp { background-color: var(--bg-color) !important; }
        
        .login-card {
            background-color: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-top: 4px solid #1E60FF !important; /* Swiss Blue Header */
            box-shadow: 8px 8px 0px var(--btn-shadow) !important;
            padding: 40px !important;
            margin-top: 80px !important;
        }
        .login-title {
            font-family: 'Helvetica Neue', Arial, sans-serif !important;
            font-weight: 900 !important;
            color: var(--text-color) !important;
            text-transform: uppercase;
            border-bottom: 4px solid var(--gold-text);
            padding-bottom: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Center login card using columns
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="login-title">GATEWAY SECURE</h2>', unsafe_allow_html=True)
        
        user = st.text_input("ENTER USERNAME:", placeholder="e.g. ghostkwebb", key="login_username")
        pwd = st.text_input("ENTER PASSWORD:", type="password", placeholder="••••••••", key="login_password")
        
        st.write("")
        # Stark white access button
        if st.button("ACCESS SYSTEM", use_container_width=True, key="login_submit"):
            creds = {
                "carlos_krause": ("password123", False), # RM Standard
                "ghostkwebb": ("Sharadmayank1!#", True), # Dev Admin
                "dev_admin": ("adminpassword", True)     # Dev Admin
            }
            
            if user in creds and pwd == creds[user][0]:
                st.session_state.authenticated = True
                st.session_state.is_dev = creds[user][1]
                st.toast("ACCESS GRANTED.")
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID CREDENTIALS.")
        st.markdown('</div>', unsafe_allow_html=True)

def check_auth():
    """Halt page execution securely if not authenticated."""
    init_auth()
    if not st.session_state.authenticated:
        login_screen()
        st.stop() 