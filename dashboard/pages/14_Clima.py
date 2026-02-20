import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data import load_ventas
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, SAGE_GREEN, RED, ORANGE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct, sidebar_date_slicer, filter_by_date
from ai_chat import ai_chat_section

apply_theme()
st.title("Impacto del Clima")

# ── Load & filter ─────────────────────────────────────────────────────────────
df = load_ventas()
df["fecha"] = pd.to_datetime(df["fecha"])
start_date, end_date = sidebar_date_slicer("clima")
df = filter_by_date(df, "fecha", start_date, end_date)

# Filter rows with clima data
df = df[df["temperatura_promedio"].notna()].copy()
df["kg_por_pedido"] = df["kg_totales"] / df["pedidos_totales"].replace(0, float("nan"))

if df.empty:
    st.warning("No hay datos de clima para el periodo seleccionado.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
avg_temp = df["temperatura_promedio"].mean()
avg_pedidos = df["pedidos_totales"].mean()
avg_kg = df["kg_totales"].mean()
avg_kg_ped = df["kg_por_pedido"].mean()

kpi_row([
    ("Temp. Prom.", f"{avg_temp:.1f} C"),
    ("Pedidos/dia Prom.", f"{avg_pedidos:.0f}"),
    ("KG/dia Prom.", f"{avg_kg:.0f}"),
    ("KG/Pedido Prom.", f"{avg_kg_ped:.1f}"),
])

st.divider()

# ── Scatter: Temperatura vs metricas ─────────────────────────────────────────
st.subheader("Temperatura vs Ventas")

metric_opts = {
    "Pedidos (Q)": "pedidos_totales",
    "KG": "kg_totales",
    "KG/Pedido": "kg_por_pedido",
    "Venta USD": "venta_total_usd",
}
sel_metric = st.radio("Metrica", list(metric_opts.keys()), horizontal=True)
y_col = metric_opts[sel_metric]

fig_scatter = px.scatter(
    df, x="temperatura_promedio", y=y_col,
    color="estacion" if "estacion" in df.columns else None,
    labels={"temperatura_promedio": "Temperatura Promedio (C)", y_col: sel_metric},
    color_discrete_sequence=COLORS,
    opacity=0.6,
)
styled_fig(fig_scatter, f"{sel_metric} vs Temperatura")
st.plotly_chart(fig_scatter, width='stretch')

st.divider()

# ── Bar: Por categoria de temperatura ────────────────────────────────────────
st.subheader("Metricas por Categoria de Temperatura")

if "categoria_temperatura" in df.columns:
    temp_order = ["Muy frio", "Frio", "Templado", "Calido", "Muy calido"]
    temp_agg = df.groupby("categoria_temperatura", as_index=False).agg(
        dias=("fecha", "count"),
        pedidos_prom=("pedidos_totales", "mean"),
        kg_prom=("kg_totales", "mean"),
        kg_por_pedido_prom=("kg_por_pedido", "mean"),
        usd_prom=("venta_total_usd", "mean"),
        delivery_prom=("pedidos_delivery", "mean"),
        local_prom=("pedidos_local", "mean"),
        mostrador_prom=("pedidos_mostrador", "mean"),
    )
    temp_agg["categoria_temperatura"] = pd.Categorical(
        temp_agg["categoria_temperatura"], categories=temp_order, ordered=True
    )
    temp_agg = temp_agg.sort_values("categoria_temperatura")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(temp_agg, x="categoria_temperatura", y="pedidos_prom",
                     color="categoria_temperatura", color_discrete_sequence=COLORS,
                     labels={"categoria_temperatura": "", "pedidos_prom": "Pedidos/dia"})
        fig.update_layout(showlegend=False)
        styled_fig(fig, "Pedidos Promedio por Temperatura")
        st.plotly_chart(fig, width='stretch')

    with c2:
        fig = px.bar(temp_agg, x="categoria_temperatura", y="kg_por_pedido_prom",
                     color="categoria_temperatura", color_discrete_sequence=COLORS,
                     labels={"categoria_temperatura": "", "kg_por_pedido_prom": "KG/Pedido"})
        fig.update_layout(showlegend=False)
        styled_fig(fig, "KG/Pedido Promedio por Temperatura")
        st.plotly_chart(fig, width='stretch')

    # Delivery vs Local/Mostrador por temperatura
    st.subheader("Delivery vs Local/Mostrador por Temperatura")
    channel_df = temp_agg[["categoria_temperatura", "delivery_prom", "local_prom", "mostrador_prom"]].copy()
    channel_melted = channel_df.melt(
        id_vars="categoria_temperatura",
        value_vars=["delivery_prom", "local_prom", "mostrador_prom"],
        var_name="Canal", value_name="Pedidos/dia",
    )
    channel_melted["Canal"] = channel_melted["Canal"].map({
        "delivery_prom": "Delivery",
        "local_prom": "Local",
        "mostrador_prom": "Mostrador",
    })
    fig_ch = px.bar(channel_melted, x="categoria_temperatura", y="Pedidos/dia",
                    color="Canal", barmode="group",
                    labels={"categoria_temperatura": "Temperatura"},
                    color_discrete_sequence=[TEAL, DARK_BLUE, SAGE_GREEN])
    styled_fig(fig_ch, "Canal de Venta por Temperatura")
    st.plotly_chart(fig_ch, width='stretch')

st.divider()

# ── Precipitaciones ──────────────────────────────────────────────────────────
st.subheader("Impacto de Precipitaciones")

if "categoria_precipitacion" in df.columns:
    rain_agg = df.groupby("categoria_precipitacion", as_index=False).agg(
        dias=("fecha", "count"),
        pedidos_prom=("pedidos_totales", "mean"),
        kg_prom=("kg_totales", "mean"),
        kg_por_pedido_prom=("kg_por_pedido", "mean"),
        delivery_prom=("pedidos_delivery", "mean"),
    )
    rain_agg = rain_agg.sort_values("pedidos_prom", ascending=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_r = px.bar(rain_agg, x="pedidos_prom", y="categoria_precipitacion",
                       orientation="h", color="categoria_precipitacion",
                       color_discrete_sequence=COLORS,
                       labels={"categoria_precipitacion": "", "pedidos_prom": "Pedidos/dia"})
        fig_r.update_layout(showlegend=False)
        styled_fig(fig_r, "Pedidos por Precipitacion")
        st.plotly_chart(fig_r, width='stretch')

    with c2:
        fig_r2 = px.bar(rain_agg, x="kg_por_pedido_prom", y="categoria_precipitacion",
                        orientation="h", color="categoria_precipitacion",
                        color_discrete_sequence=COLORS,
                        labels={"categoria_precipitacion": "", "kg_por_pedido_prom": "KG/Pedido"})
        fig_r2.update_layout(showlegend=False)
        styled_fig(fig_r2, "KG/Pedido por Precipitacion")
        st.plotly_chart(fig_r2, width='stretch')

st.divider()

# ── USD por temperatura ──────────────────────────────────────────────────────
st.subheader("Venta USD por Temperatura")

if "categoria_temperatura" in df.columns and "venta_total_usd" in df.columns:
    fig_usd = px.bar(temp_agg, x="categoria_temperatura", y="usd_prom",
                     color="categoria_temperatura", color_discrete_sequence=COLORS,
                     labels={"categoria_temperatura": "", "usd_prom": "Venta USD/dia"})
    fig_usd.update_layout(showlegend=False)
    styled_fig(fig_usd, "Venta USD Promedio/dia por Temperatura")
    st.plotly_chart(fig_usd, width='stretch')

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Resumen por Categoria de Temperatura")

if "categoria_temperatura" in df.columns:
    for col in ["pedidos_prom", "kg_prom", "kg_por_pedido_prom", "usd_prom",
                "delivery_prom", "local_prom", "mostrador_prom"]:
        if col in temp_agg.columns:
            temp_agg[col] = temp_agg[col].round(1)
    temp_agg.columns = [
        "Temperatura", "Dias", "Pedidos/dia", "KG/dia", "KG/Ped",
        "USD/dia", "Delivery/dia", "Local/dia", "Mostrador/dia",
    ]
    st.dataframe(temp_agg, width='stretch', hide_index=True)


# -- AI Chat --
ai_chat_section(df, "clima", "Impacto del clima: temperatura vs pedidos, KG, delivery, precipitaciones")
