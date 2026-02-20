import streamlit as st

st.set_page_config(
    page_title="Ainara Analytics",
    page_icon="\U0001f366",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Authentication gate ───────────────────────────────────────────────────
from auth import require_auth, logout_button

if not require_auth():
    st.stop()

# ── Authenticated: show dashboard ─────────────────────────────────────────
logout_button()

pages = st.navigation([
    st.Page("pages/01_Ventas.py",          title="Ventas",          icon="\U0001f4ca", default=True),
    st.Page("pages/02_Clientes.py",        title="Clientes",        icon="\U0001f465"),
    st.Page("pages/03_Pedidos.py",         title="Pedidos",         icon="\U0001f4e6"),
    st.Page("pages/04_Productos.py",       title="Productos",       icon="\U0001f366"),
    st.Page("pages/05_Sabores.py",         title="Sabores",         icon="\U0001f36c"),
    st.Page("pages/14_Clima.py",           title="Clima",           icon="\U0001f321\ufe0f"),
    st.Page("pages/06_PnL.py",            title="PnL",             icon="\U0001f4b0"),
    st.Page("pages/07_Cash_Flow.py",       title="Cash Flow",       icon="\U0001f4b5"),
    st.Page("pages/08_Egresos.py",         title="Egresos",         icon="\U0001f4c9"),
    st.Page("pages/10_Margenes.py",        title="Margenes",        icon="\U0001f4c8"),
    st.Page("pages/09_RFM.py",            title="RFM",             icon="\U0001f3af"),
    st.Page("pages/11_Puntos.py",          title="Puntos",          icon="\U00002b50"),
    st.Page("pages/12_Zonas.py",           title="Zonas",           icon="\U0001f4cd"),
    st.Page("pages/13_Clientes_Nuevos.py", title="Clientes Nuevos", icon="\U0001f195"),
])

pages.run()
