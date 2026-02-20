# ════════════════════════════════════════════════════════════════════════════
# Authentication — CSV (local) + st.secrets (Streamlit Cloud)
# ════════════════════════════════════════════════════════════════════════════
#
# LOCAL: reads from dashboard/users.csv (username,password_hash,name)
# CLOUD: reads from st.secrets (configured in Streamlit Cloud dashboard)
#
# To add a user, generate SHA-256 hash:
#   python -c "import hashlib; print(hashlib.sha256('MI_CLAVE'.encode()).hexdigest())"
# ════════════════════════════════════════════════════════════════════════════
import hashlib
import csv
from pathlib import Path
import streamlit as st

_USERS_FILE = Path(__file__).parent / "users.csv"


def _load_users() -> dict:
    """Load users from CSV or st.secrets. Returns {username: {password_hash, name}}."""
    users = {}

    # 1. Try st.secrets (Streamlit Cloud)
    try:
        if "users" in st.secrets:
            for username, user_data in st.secrets["users"].items():
                users[username] = {
                    "password_hash": user_data["password_hash"],
                    "name": user_data["name"],
                }
            return users
    except Exception:
        pass

    # 2. Fallback: CSV file (local)
    if not _USERS_FILE.exists():
        return users
    with open(_USERS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users[row["username"].strip()] = {
                "password_hash": row["password_hash"].strip(),
                "name": row["name"].strip(),
            }
    return users


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _check_credentials(username: str, password: str) -> tuple[bool, str]:
    """Check username/password. Returns (success, display_name)."""
    users = _load_users()
    user = users.get(username)
    if user and user["password_hash"] == _hash_password(password):
        return True, user["name"]
    return False, ""


def login_page():
    """Render the login page. Returns True if authenticated."""
    if st.session_state.get("authenticated"):
        return True

    # Center the login form
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oxygen:wght@400;700&family=Lato:wght@300;400;700&display=swap');
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #e8f4f5 0%, #f0f3f5 50%, #eaf0f2 100%);
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logo / Header
        st.markdown(
            '<div style="text-align:center;">'
            '<h1 style="font-family:Oxygen,sans-serif;color:#02777d;font-size:2.5rem;margin-bottom:0;">'
            '🍦 Ainara Analytics</h1>'
            '<p style="font-family:Lato,sans-serif;color:#7a8a8a;font-size:1rem;margin-top:4px;">'
            'Dashboard de Gestion</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Login form
        with st.form("login_form"):
            st.markdown(
                '<p style="font-family:Oxygen,sans-serif;color:#467999;font-weight:700;'
                'font-size:1.1rem;margin-bottom:8px;">Iniciar Sesion</p>',
                unsafe_allow_html=True,
            )
            username = st.text_input("Usuario", placeholder="usuario")
            password = st.text_input("Clave", type="password", placeholder="clave")
            submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

        if submitted:
            if username and password:
                ok, name = _check_credentials(username.strip().lower(), password)
                if ok:
                    st.session_state["authenticated"] = True
                    st.session_state["user_name"] = name
                    st.session_state["user_id"] = username.strip().lower()
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos.")
            else:
                st.warning("Ingresa usuario y clave.")

    return False


def logout_button():
    """Render a logout button in the sidebar."""
    with st.sidebar:
        st.markdown("---")
        name = st.session_state.get("user_name", "")
        st.markdown(
            f'<p style="font-family:Lato,sans-serif;color:#467999;font-size:13px;">'
            f'Sesion: <b>{name}</b></p>',
            unsafe_allow_html=True,
        )
        if st.button("Cerrar Sesion", key="_logout"):
            for key in ["authenticated", "user_name", "user_id"]:
                st.session_state.pop(key, None)
            st.rerun()


def require_auth():
    """Call at the top of app.py. Shows login if not authenticated, returns True when OK."""
    return login_page()
