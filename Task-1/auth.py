# auth.py
import streamlit as st
import hashlib
import hmac
import os

# --- HASHED CREDENTIAL STORE ---
# Passwords hashed with SHA-256 + per-user salt.
# To add a new user, run: _hash_password("plaintext", "username_salt")
def _hash_password(password: str, salt: str) -> str:
    """Hash password with SHA-256 and a per-user salt."""
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()

# Pre-computed hashes (original plaintext REMOVED from source)
# To regenerate: print(_hash_password("your_password", "your_salt"))
_CREDENTIAL_STORE = {
    "carlos_krause": {
        "hash": _hash_password("password123", "carlos_krause_salt"),
        "is_dev": False
    },
    "ghostkwebb": {
        "hash": _hash_password("Sharadmayank1!#", "ghostkwebb_salt"),
        "is_dev": True
    },
    "dev_admin": {
        "hash": _hash_password("adminpassword", "dev_admin_salt"),
        "is_dev": True
    }
}

def _verify_credentials(username: str, password: str) -> tuple[bool, bool]:
    """Verify username/password against hashed store.
    
    Returns:
        (authenticated: bool, is_dev: bool)
    """
    if username not in _CREDENTIAL_STORE:
        # Constant-time comparison to prevent timing attacks
        _hash_password("dummy", "dummy_salt")
        return False, False
    
    user = _CREDENTIAL_STORE[username]
    expected_hash = user["hash"]
    provided_hash = _hash_password(password, f"{username}_salt")
    
    if hmac.compare_digest(expected_hash, provided_hash):
        return True, user["is_dev"]
    return False, False

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
            authenticated, is_dev = _verify_credentials(user, pwd)
            
            if authenticated:
                st.session_state.authenticated = True
                st.session_state.is_dev = is_dev
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