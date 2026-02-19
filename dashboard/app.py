import os
import sys

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DASHBOARD_DIR, "..", "ainara.duckdb")
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from theme import apply_theme, styled_fig, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd

# ── Data loaders ──────────────────────────────────────────────────────────────

def _conn():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(ttl=300)
def load_table(name: str, date_col: str = None, since: str = None) -> pd.DataFrame:
    conn = _conn()
    query = f'SELECT * FROM main."{name}"'
    if date_col and since:
        query += f" WHERE {date_col} >= '{since}'"
    df = conn.execute(query).df()
    conn.close()
    return df


SINCE = "2023-01-01"

def load_ventas():        return load_table("fct_ventas_diarias", "fecha", SINCE)
def load_pedidos():       return load_table("fct_pedidos", "fecha", SINCE)
def load_clientes():      return load_table("dim_clientes")
def load_productos():     return load_table("rpt_productos_vendidos")
def load_sabores():       return load_table("rpt_sabores")
def load_pnl():           return load_table("rpt_pnl", "mes", SINCE)
def load_cash_flow():     return load_table("rpt_cash_flow", "mes", SINCE)
def load_egresos():       return load_table("rpt_egresos", "mes", SINCE)
def load_rfm():           return load_table("rpt_rfm")
def load_margenes():      return load_table("rpt_margenes", "mes", SINCE)
def load_puntos():        return load_table("rpt_puntos")
def load_zonas():         return load_table("rpt_zonas")
def load_clientes_nuevos(): return load_table("rpt_clientes_nuevos", "mes", SINCE)


# ── Page config (redirect to Ventas) ─────────────────────────────────────────

st.set_page_config(
    page_title="Ainara Analytics",
    page_icon="🍦",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# No home page content — Ventas is the default landing page
st.switch_page("pages/01_Ventas.py")
