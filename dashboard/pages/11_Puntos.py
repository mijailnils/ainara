import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_puntos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Puntos - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Programa de Puntos")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_puntos()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_acumulados = int(df["puntos_acumulados"].sum())
total_canjeados = int(df["puntos_canjeados"].sum())
total_saldo = int(df["saldo_vigente"].sum()) if "saldo_vigente" in df.columns else 0
total_activos = int(df["is_activo_puntos"].sum()) if "is_activo_puntos" in df.columns else 0

kpi_row([
    ("Puntos Acumulados", f"{total_acumulados:,}"),
    ("Puntos Canjeados", f"{total_canjeados:,}"),
    ("Saldo Vigente", f"{total_saldo:,}"),
    ("Clientes Activos", f"{total_activos:,}"),
])

st.divider()

# ── Bar chart: top 15 by puntos_acumulados ───────────────────────────────────
st.subheader("Top 15 Clientes por Puntos Acumulados")

top15 = df.nlargest(15, "puntos_acumulados").sort_values("puntos_acumulados")

fig_top = px.bar(
    top15, x="puntos_acumulados", y="nombre", orientation="h",
    color="segmento_cliente",
    labels={"puntos_acumulados": "Puntos Acumulados", "nombre": "Cliente", "segmento_cliente": "Segmento"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_top, "Top 15 por Puntos Acumulados")
st.plotly_chart(fig_top, use_container_width=True)

st.divider()

# ── Pie chart: is_activo_puntos distribution ─────────────────────────────────
st.subheader("Actividad del Programa de Puntos")

activo_counts = df["is_activo_puntos"].map({True: "Activo", False: "Inactivo"}).value_counts().reset_index()
activo_counts.columns = ["Estado", "Clientes"]

fig_activo = px.pie(
    activo_counts, names="Estado", values="Clientes",
    color_discrete_sequence=[TEAL, DARK_BLUE],
)
styled_fig(fig_activo, "Clientes Activos vs Inactivos en Puntos")
fig_activo.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig_activo, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Puntos")

display_cols = [
    "cliente_id", "nombre", "segmento_cliente",
    "puntos_acumulados", "puntos_canjeados", "saldo_vigente",
    "ratio_canje", "total_movimientos",
    "is_activo_puntos",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("puntos_acumulados", ascending=False),
    use_container_width=True,
    hide_index=True,
)
