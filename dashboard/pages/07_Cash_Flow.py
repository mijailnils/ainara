import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app import load_cash_flow
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, RED
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Cash Flow - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Flujo de Caja")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_cash_flow()
df["mes"] = pd.to_datetime(df["mes"])
df = df.sort_values("mes")

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_inflows = df["total_inflows"].sum()
total_outflows = df["total_outflows"].sum()
total_flujo_neto = df["flujo_neto"].sum()
total_flujo_neto_usd = df["flujo_neto_usd"].sum() if "flujo_neto_usd" in df.columns else 0

kpi_row([
    ("Total Inflows ($)", fmt_ars(total_inflows)),
    ("Total Outflows ($)", fmt_ars(total_outflows)),
    ("Flujo Neto ($)", fmt_ars(total_flujo_neto)),
    ("Flujo Neto (USD)", fmt_usd(total_flujo_neto_usd)),
])

st.divider()

# ── Monthly stacked bar: inflows vs outflows ─────────────────────────────────
st.subheader("Inflows vs Outflows Mensuales")

fig_cf = go.Figure()
fig_cf.add_bar(
    x=df["mes"], y=df["total_inflows"],
    name="Inflows", marker_color=TEAL,
)
fig_cf.add_bar(
    x=df["mes"], y=-df["total_outflows"],
    name="Outflows", marker_color=RED,
)
styled_fig(fig_cf, "Flujo de Caja Mensual")
fig_cf.update_layout(
    barmode="relative",
    yaxis_title="Monto ($)",
    xaxis_title="Mes",
)
st.plotly_chart(fig_cf, use_container_width=True)

st.divider()

# ── Line chart: flujo_neto_acumulado ──────────────────────────────────────────
st.subheader("Flujo Neto Acumulado")

if "flujo_neto_acumulado" in df.columns:
    fig_acum = px.line(
        df, x="mes", y="flujo_neto_acumulado",
        markers=True,
        labels={"mes": "Mes", "flujo_neto_acumulado": "Flujo Neto Acumulado ($)"},
    )
    styled_fig(fig_acum, "Flujo Neto Acumulado")
    st.plotly_chart(fig_acum, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Cash Flow")

display_cols = [
    "mes", "cobros_efectivo", "cobros_mp_neto", "cobros_transferencia",
    "total_inflows", "total_outflows", "flujo_neto", "flujo_neto_acumulado",
    "total_inflows_usd", "total_outflows_usd", "flujo_neto_usd",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("mes", ascending=False),
    use_container_width=True,
    hide_index=True,
)
