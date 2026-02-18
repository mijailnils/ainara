import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_productos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Productos - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Productos")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_productos()

# ── Horizontal bar chart: veces_vendido top 20 ───────────────────────────────
st.subheader("Top 20 Productos por Unidades Vendidas")

top20_units = df.nlargest(20, "veces_vendido").sort_values("veces_vendido")

fig_units = px.bar(
    top20_units, x="veces_vendido", y="producto", orientation="h",
    color="categoria",
    labels={"veces_vendido": "Veces Vendido", "producto": "Producto", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_units, "Top 20 por Unidades Vendidas")
fig_units.update_layout(height=600)
st.plotly_chart(fig_units, use_container_width=True)

st.divider()

# ── Horizontal bar chart: ingreso_estimado top 20 ────────────────────────────
st.subheader("Top 20 Productos por Ingreso Estimado")

top20_rev = df.nlargest(20, "ingreso_estimado").sort_values("ingreso_estimado")

fig_rev = px.bar(
    top20_rev, x="ingreso_estimado", y="producto", orientation="h",
    color="categoria",
    labels={"ingreso_estimado": "Ingreso Estimado ($)", "producto": "Producto", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_rev, "Top 20 por Ingreso Estimado")
fig_rev.update_layout(height=600)
st.plotly_chart(fig_rev, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Productos")

display_cols = [
    "ranking", "producto", "categoria", "precio_base",
    "cantidad_gustos", "veces_vendido", "pedidos_distintos",
    "ingreso_estimado", "porcentaje_del_total",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("ranking"),
    use_container_width=True,
    hide_index=True,
)
