import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_clientes
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Clientes - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Clientes")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_clientes()
buyers = df[df["total_pedidos"] > 0].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_con_compras = len(buyers)
avg_ticket = buyers["ticket_promedio"].mean() if len(buyers) > 0 else 0
avg_kg = buyers["kg_total"].mean() if len(buyers) > 0 else 0

kpi_row([
    ("Clientes con Compras", f"{total_con_compras:,}"),
    ("Ticket Promedio", fmt_ars(avg_ticket)),
    ("KG Promedio", f"{avg_kg:,.1f} kg"),
])

st.divider()

# ── Pie chart: segmento_cliente ───────────────────────────────────────────────
st.subheader("Distribucion por Segmento")

seg_counts = buyers["segmento_cliente"].value_counts().reset_index()
seg_counts.columns = ["Segmento", "Clientes"]

fig_pie = px.pie(
    seg_counts, names="Segmento", values="Clientes",
    color_discrete_sequence=COLORS,
)
styled_fig(fig_pie, "Segmentos de Clientes")
fig_pie.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Top 15 by total_gastado (horizontal) ──────────────────────────────────────
st.subheader("Top 15 Clientes por Gasto Total")

top15 = buyers.nlargest(15, "total_gastado")[["nombre", "total_gastado", "segmento_cliente"]].copy()

fig_top = px.bar(
    top15.sort_values("total_gastado"),
    x="total_gastado", y="nombre", orientation="h",
    color="segmento_cliente",
    labels={"total_gastado": "Gasto Total ($)", "nombre": "Cliente", "segmento_cliente": "Segmento"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_top, "Top 15 Clientes por Gasto")
st.plotly_chart(fig_top, use_container_width=True)

st.divider()

# ── tipo_retiro_preferido breakdown ───────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Tipo de Retiro Preferido")
    retiro = buyers["tipo_retiro_preferido"].value_counts().reset_index()
    retiro.columns = ["Tipo", "Clientes"]
    fig_r = px.bar(
        retiro, x="Tipo", y="Clientes",
        color="Tipo", color_discrete_sequence=COLORS,
        labels={"Tipo": "Tipo de Retiro", "Clientes": "Clientes"},
    )
    fig_r.update_layout(showlegend=False)
    styled_fig(fig_r, "Tipo de Retiro Preferido")
    st.plotly_chart(fig_r, use_container_width=True)

with col2:
    st.subheader("Tipo de Pago Preferido")
    pago = buyers["tipo_pago_preferido"].value_counts().reset_index()
    pago.columns = ["Pago", "Clientes"]
    fig_p = px.bar(
        pago, x="Pago", y="Clientes",
        color="Pago", color_discrete_sequence=COLORS,
        labels={"Pago": "Tipo de Pago", "Clientes": "Clientes"},
    )
    fig_p.update_layout(showlegend=False)
    styled_fig(fig_p, "Tipo de Pago Preferido")
    st.plotly_chart(fig_p, use_container_width=True)

st.divider()

# ── Filterable dataframe ──────────────────────────────────────────────────────
st.subheader("Tabla de Clientes")

seg_filter = st.multiselect(
    "Filtrar por segmento",
    options=sorted(df["segmento_cliente"].dropna().unique()),
    default=sorted(df["segmento_cliente"].dropna().unique()),
)

search = st.text_input("Buscar cliente por nombre")

show = df[df["segmento_cliente"].isin(seg_filter)].copy()
if search:
    show = show[show["nombre"].str.contains(search, case=False, na=False)]

display_cols = [
    "cliente_id", "nombre", "email", "barrio", "total_pedidos",
    "total_gastado", "ticket_promedio", "kg_total",
    "dias_desde_ultimo_pedido", "segmento_cliente",
    "tipo_retiro_preferido", "tipo_pago_preferido",
]
available_cols = [c for c in display_cols if c in show.columns]
st.dataframe(show[available_cols], use_container_width=True, hide_index=True)
