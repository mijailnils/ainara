import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app import load_ventas
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Ventas - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Ventas Diarias")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_ventas()
df["fecha"] = pd.to_datetime(df["fecha"])

# ── Date range filter ─────────────────────────────────────────────────────────
min_date = df["fecha"].min().date()
max_date = df["fecha"].max().date()

col_f1, col_f2 = st.columns(2)
start_date = col_f1.date_input("Desde", value=min_date, min_value=min_date, max_value=max_date)
end_date = col_f2.date_input("Hasta", value=max_date, min_value=min_date, max_value=max_date)

mask = (df["fecha"].dt.date >= start_date) & (df["fecha"].dt.date <= end_date)
filtered = df[mask].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
venta_total = filtered["venta_total"].sum()
pedidos_totales = int(filtered["pedidos_totales"].sum())
ticket_promedio = filtered["ticket_promedio"].mean() if len(filtered) > 0 else 0
kg_totales = filtered["kg_totales"].sum()

kpi_row([
    ("Ventas Totales", fmt_ars(venta_total)),
    ("Pedidos Totales", f"{pedidos_totales:,}"),
    ("Ticket Promedio", fmt_ars(ticket_promedio)),
    ("KG Totales", f"{kg_totales:,.0f} kg"),
])

st.divider()

# ── Tabs: ARS / USD ──────────────────────────────────────────────────────────
tab_ars, tab_usd = st.tabs(["ARS", "USD"])

with tab_ars:
    fig = px.line(
        filtered.sort_values("fecha"), x="fecha", y="venta_total",
        markers=True,
        labels={"fecha": "Fecha", "venta_total": "Ventas ($)"},
    )
    styled_fig(fig, "Ventas Diarias (ARS)")
    st.plotly_chart(fig, use_container_width=True)

with tab_usd:
    if "venta_total_usd" in filtered.columns and filtered["venta_total_usd"].notna().any():
        fig_usd = px.line(
            filtered.sort_values("fecha"), x="fecha", y="venta_total_usd",
            markers=True,
            labels={"fecha": "Fecha", "venta_total_usd": "Ventas (U$D)"},
        )
        styled_fig(fig_usd, "Ventas Diarias (USD)")
        st.plotly_chart(fig_usd, use_container_width=True)
    else:
        st.info("No hay datos de tipo de cambio disponibles.")

st.divider()

# ── Payment method stacked bar by month ───────────────────────────────────────
st.subheader("Mix de Pagos por Mes")

filtered["mes_str"] = pd.to_datetime(filtered["fecha"]).dt.to_period("M").astype(str)

monthly_pay = (
    filtered.groupby("mes_str", as_index=False)
    .agg(
        Efectivo=("venta_efectivo", "sum"),
        MercadoPago=("venta_mercadopago", "sum"),
        Transferencia=("venta_transferencia", "sum"),
    )
    .sort_values("mes_str")
)

pay_melted = monthly_pay.melt(id_vars="mes_str", var_name="Medio de Pago", value_name="Ventas")

fig_pay = px.bar(
    pay_melted, x="mes_str", y="Ventas", color="Medio de Pago",
    barmode="stack",
    labels={"mes_str": "Mes", "Ventas": "Ventas ($)"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_pay, "Ventas por Medio de Pago")
st.plotly_chart(fig_pay, use_container_width=True)

st.divider()

# ── Pedidos by estacion ───────────────────────────────────────────────────────
st.subheader("Pedidos por Estacion")

if "estacion" in filtered.columns:
    estacion_df = filtered.groupby("estacion", as_index=False)["pedidos_totales"].sum()
    estacion_order = ["Verano", "Otoño", "Invierno", "Primavera"]
    estacion_df["estacion"] = pd.Categorical(estacion_df["estacion"], categories=estacion_order, ordered=True)
    estacion_df = estacion_df.sort_values("estacion")

    fig_est = px.bar(
        estacion_df, x="estacion", y="pedidos_totales",
        labels={"estacion": "Estacion", "pedidos_totales": "Pedidos"},
        color="estacion", color_discrete_sequence=COLORS,
    )
    fig_est.update_layout(showlegend=False)
    styled_fig(fig_est, "Pedidos por Estacion")
    st.plotly_chart(fig_est, use_container_width=True)

st.divider()

# ── Pedidos by temporada ──────────────────────────────────────────────────────
st.subheader("Pedidos por Temporada")

if "temporada" in filtered.columns:
    temporada_df = filtered.groupby("temporada", as_index=False)["pedidos_totales"].sum()
    temp_order = ["Alta", "Media", "Baja"]
    temporada_df["temporada"] = pd.Categorical(temporada_df["temporada"], categories=temp_order, ordered=True)
    temporada_df = temporada_df.sort_values("temporada")

    fig_temp = px.bar(
        temporada_df, x="temporada", y="pedidos_totales",
        labels={"temporada": "Temporada", "pedidos_totales": "Pedidos"},
        color="temporada", color_discrete_sequence=COLORS,
    )
    fig_temp.update_layout(showlegend=False)
    styled_fig(fig_temp, "Pedidos por Temporada")
    st.plotly_chart(fig_temp, use_container_width=True)
