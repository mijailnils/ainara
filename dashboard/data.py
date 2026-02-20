# ════════════════════════════════════════════════════════════════════════════
# Data loaders — Parquet files (works locally and on Streamlit Cloud)
# ════════════════════════════════════════════════════════════════════════════
import os
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SINCE = "2023-01-01"
UNTIL = "2025-12-31"


@st.cache_data(ttl=300)
def load_table(name: str, date_col: str = None, since: str = None, until: str = None) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{name}.parquet")
    df = pd.read_parquet(path)
    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        if since:
            df = df[df[date_col] >= since]
        if until:
            df = df[df[date_col] <= until]
    return df


def load_ventas():        return load_table("fct_ventas_diarias", "fecha", SINCE, UNTIL)
def load_pedidos():       return load_table("fct_pedidos", "fecha", SINCE, UNTIL)
def load_clientes():      return load_table("dim_clientes")
def load_productos():     return load_table("rpt_productos_vendidos")
def load_sabores():       return load_table("rpt_sabores")
def load_pnl():           return load_table("rpt_pnl", "mes", SINCE, UNTIL)
def load_cash_flow():     return load_table("rpt_cash_flow", "mes", SINCE, UNTIL)
def load_egresos():       return load_table("rpt_egresos", "mes", SINCE, UNTIL)
def load_rfm():           return load_table("rpt_rfm")
def load_margenes():      return load_table("rpt_margenes", "mes", SINCE, UNTIL)
def load_puntos():        return load_table("rpt_puntos")
def load_zonas():         return load_table("rpt_zonas")
def load_clientes_nuevos(): return load_table("rpt_clientes_nuevos", "mes", SINCE, UNTIL)
