import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from data import load_zonas
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct
from ai_chat import ai_chat_section

apply_theme()
st.title("Zonas de Delivery")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_zonas()
df["zona_label"] = "Zona " + df["zona_id"].astype(str)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_pedidos = int(df["total_pedidos"].sum())
total_kg = df["kg_totales"].sum() if "kg_totales" in df.columns else 0
total_ventas = df["venta_total"].sum()
total_ventas_usd = df["venta_total_usd"].sum() if "venta_total_usd" in df.columns else 0

kpi_row([
    ("Pedidos (Q)", f"{total_pedidos:,}"),
    ("KG", f"{total_kg:,.0f}"),
    ("Ventas ($)", fmt_ars(total_ventas)),
    ("Ventas (USD)", fmt_usd(total_ventas_usd)),
])

st.divider()

# ── Bar chart: total_pedidos by zona ─────────────────────────────────────────
st.subheader("Pedidos por Zona")

fig_pedidos = px.bar(
    df.sort_values("total_pedidos", ascending=False),
    x="zona_label", y="total_pedidos",
    color="zona_label", color_discrete_sequence=COLORS,
    labels={"zona_label": "Zona", "total_pedidos": "Total Pedidos"},
)
fig_pedidos.update_layout(showlegend=False)
styled_fig(fig_pedidos, "Pedidos por Zona")
st.plotly_chart(fig_pedidos, width='stretch')

st.divider()

# ── Bar chart: venta_total by zona ───────────────────────────────────────────
st.subheader("Ventas por Zona")

fig_ventas = px.bar(
    df.sort_values("venta_total", ascending=False),
    x="zona_label", y="venta_total",
    color="zona_label", color_discrete_sequence=COLORS,
    labels={"zona_label": "Zona", "venta_total": "Venta Total ($)"},
)
fig_ventas.update_layout(showlegend=False)
styled_fig(fig_ventas, "Ventas por Zona")
st.plotly_chart(fig_ventas, width='stretch')

st.divider()

# ── Metrics table ────────────────────────────────────────────────────────────
st.subheader("Metricas por Zona")

metrics_cols = [
    "zona_label", "total_pedidos", "total_clientes", "venta_total",
    "venta_total_usd", "kg_totales", "ticket_promedio",
    "demora_promedio_real", "distancia_promedio_real",
    "precio_envio", "pct_pedidos_total",
]
available_cols = [c for c in metrics_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("total_pedidos", ascending=False),
    width='stretch',
    hide_index=True,
)

st.divider()

# ── Full data table ──────────────────────────────────────────────────────────
st.subheader("Tabla Completa de Zonas")

st.dataframe(
    df.sort_values("total_pedidos", ascending=False),
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(df, "zonas", "Zonas de delivery: pedidos, clientes, venta, demora, distancia")
