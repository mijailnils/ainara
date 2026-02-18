import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app import load_pnl
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, SAGE_GREEN, RED, ORANGE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="PnL - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Estado de Resultados (PnL)")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_pnl()
df["mes"] = pd.to_datetime(df["mes"])
df = df.sort_values("mes")

# ── Waterfall chart: latest month ─────────────────────────────────────────────
st.subheader("Waterfall - Ultimo Mes")

latest = df.iloc[-1]

waterfall_items = [
    ("Ingresos", latest["ingresos_totales"]),
    ("COGS", -latest["cogs_total"]),
    ("Gastos Op.", -latest["total_gastos_operativos"]),
    ("Comisiones", -latest["total_comisiones"]),
    ("Delivery", -latest["costo_delivery"]),
]

labels = [item[0] for item in waterfall_items] + ["Resultado"]
values = [item[1] for item in waterfall_items] + [latest["resultado_operativo"]]
measures = ["relative"] * len(waterfall_items) + ["total"]

fig_wf = go.Figure(go.Waterfall(
    name="PnL",
    orientation="v",
    measure=measures,
    x=labels,
    y=values,
    connector={"line": {"color": "#e0e0e0"}},
    increasing={"marker": {"color": TEAL}},
    decreasing={"marker": {"color": RED}},
    totals={"marker": {"color": DARK_BLUE}},
    textposition="outside",
    text=[fmt_ars(abs(v)) for v in values],
))
styled_fig(fig_wf, f"PnL - {latest['mes'].strftime('%B %Y')}")
fig_wf.update_layout(showlegend=False)
st.plotly_chart(fig_wf, use_container_width=True)

st.divider()

# ── Monthly trend: ARS / USD tabs ────────────────────────────────────────────
st.subheader("Tendencia Mensual")

tab_ars, tab_usd = st.tabs(["ARS", "USD"])

with tab_ars:
    fig_trend = go.Figure()
    fig_trend.add_scatter(x=df["mes"], y=df["ingresos_totales"], name="Ingresos", mode="lines+markers")
    fig_trend.add_scatter(x=df["mes"], y=df["cogs_total"], name="COGS", mode="lines+markers")
    fig_trend.add_scatter(x=df["mes"], y=df["resultado_operativo"], name="Resultado", mode="lines+markers")
    styled_fig(fig_trend, "Ingresos vs COGS vs Resultado (ARS)")
    st.plotly_chart(fig_trend, use_container_width=True)

with tab_usd:
    usd_cols = ["ingresos_totales_usd", "cogs_total_usd", "resultado_operativo_usd"]
    if all(c in df.columns for c in usd_cols) and df[usd_cols[0]].notna().any():
        fig_trend_usd = go.Figure()
        fig_trend_usd.add_scatter(x=df["mes"], y=df["ingresos_totales_usd"], name="Ingresos USD", mode="lines+markers")
        fig_trend_usd.add_scatter(x=df["mes"], y=df["cogs_total_usd"], name="COGS USD", mode="lines+markers")
        fig_trend_usd.add_scatter(x=df["mes"], y=df["resultado_operativo_usd"], name="Resultado USD", mode="lines+markers")
        styled_fig(fig_trend_usd, "Ingresos vs COGS vs Resultado (USD)")
        st.plotly_chart(fig_trend_usd, use_container_width=True)
    else:
        st.info("No hay datos de tipo de cambio disponibles.")

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla PnL Mensual")

display_cols = [
    "mes", "ingresos_totales", "cogs_total", "margen_bruto", "margen_bruto_pct",
    "total_gastos_operativos", "total_comisiones", "costo_delivery",
    "resultado_operativo", "resultado_operativo_pct",
    "pedidos_totales", "kg_totales",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("mes", ascending=False),
    use_container_width=True,
    hide_index=True,
)
