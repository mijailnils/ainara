import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data import load_ventas
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct, sidebar_date_slicer, filter_by_date
from ai_chat import ai_chat_section

apply_theme()
st.title("Ventas")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_ventas()
df["fecha"] = pd.to_datetime(df["fecha"])

# ── Sidebar date slicer ──────────────────────────────────────────────────────
start_date, end_date = sidebar_date_slicer("ventas")
filtered = filter_by_date(df, "fecha", start_date, end_date)

# ── KPIs: siempre Q, KG, $, USD ──────────────────────────────────────────────
total_q = int(filtered["pedidos_totales"].sum())
total_kg = filtered["kg_totales"].sum()
total_ars = filtered["venta_total"].sum()
total_usd = filtered["venta_total_usd"].sum() if "venta_total_usd" in filtered.columns else 0

kpi_row([
    ("Pedidos (Q)", f"{total_q:,}"),
    ("KG", f"{total_kg:,.0f}"),
    ("Ventas ($)", fmt_ars(total_ars)),
    ("Ventas (USD)", fmt_usd(total_usd)),
])

st.divider()

# ── Granularidad: Diario / Semanal / Mensual ─────────────────────────────────
tab_d, tab_s, tab_m = st.tabs(["Diario", "Semanal", "Mensual"])

# Preparar agrupaciones
filtered["semana_dt"] = filtered["fecha"].dt.to_period("W").apply(lambda x: x.start_time)
filtered["mes_dt"] = filtered["fecha"].dt.to_period("M").dt.to_timestamp()

AGG = {
    "pedidos_totales": "sum",
    "kg_totales": "sum",
    "venta_total": "sum",
    "venta_total_usd": "sum",
}

daily = filtered.sort_values("fecha")
weekly = filtered.groupby("semana_dt", as_index=False).agg(**{k: (k, v) for k, v in AGG.items()}).sort_values("semana_dt")
monthly = filtered.groupby("mes_dt", as_index=False).agg(**{k: (k, v) for k, v in AGG.items()}).sort_values("mes_dt")


def render_ventas(data, x_col, title_prefix):
    """Render the 4 metrics charts for a given granularity."""
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(data, x=x_col, y="pedidos_totales",
                     labels={x_col: "", "pedidos_totales": "Pedidos (Q)"},
                     color_discrete_sequence=[TEAL])
        styled_fig(fig, f"{title_prefix} — Pedidos (Q)")
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.bar(data, x=x_col, y="kg_totales",
                     labels={x_col: "", "kg_totales": "KG"},
                     color_discrete_sequence=[DARK_BLUE])
        styled_fig(fig, f"{title_prefix} — KG")
        st.plotly_chart(fig, width='stretch')

    c3, c4 = st.columns(2)
    with c3:
        fig = px.line(data, x=x_col, y="venta_total", markers=True,
                      labels={x_col: "", "venta_total": "Ventas ($)"},
                      color_discrete_sequence=[TEAL])
        styled_fig(fig, f"{title_prefix} — Ventas ($)")
        st.plotly_chart(fig, width='stretch')
    with c4:
        fig = px.line(data, x=x_col, y="venta_total_usd", markers=True,
                      labels={x_col: "", "venta_total_usd": "Ventas (USD)"},
                      color_discrete_sequence=[DARK_BLUE])
        styled_fig(fig, f"{title_prefix} — Ventas (USD)")
        st.plotly_chart(fig, width='stretch')


with tab_d:
    render_ventas(daily, "fecha", "Diario")

with tab_s:
    render_ventas(weekly, "semana_dt", "Semanal")

with tab_m:
    render_ventas(monthly, "mes_dt", "Mensual")

st.divider()

# ── Mix de pagos mensual ─────────────────────────────────────────────────────
st.subheader("Mix de Pagos por Mes")

filtered["mes_str"] = filtered["fecha"].dt.to_period("M").astype(str)
monthly_pay = (
    filtered.groupby("mes_str", as_index=False)
    .agg(
        Efectivo=("pagos_efectivo", "sum"),
        MercadoPago=("pagos_mercadopago", "sum"),
        Transferencia=("pagos_transferencia", "sum"),
    )
    .sort_values("mes_str")
)
pay_melted = monthly_pay.melt(id_vars="mes_str", var_name="Medio de Pago", value_name="Pedidos")
fig_pay = px.bar(pay_melted, x="mes_str", y="Pedidos", color="Medio de Pago",
                 barmode="stack", labels={"mes_str": "Mes", "Pedidos": "Pedidos (Q)"},
                 color_discrete_sequence=COLORS)
styled_fig(fig_pay, "Pedidos por Medio de Pago")
st.plotly_chart(fig_pay, width='stretch')

st.divider()

# ── Estacion y Temporada ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    if "estacion" in filtered.columns:
        est = filtered.groupby("estacion", as_index=False).agg(
            pedidos=("pedidos_totales", "sum"), kg=("kg_totales", "sum"),
            ars=("venta_total", "sum"), usd=("venta_total_usd", "sum"),
        )
        est_order = ["Verano", "Otoño", "Invierno", "Primavera"]
        est["estacion"] = pd.Categorical(est["estacion"], categories=est_order, ordered=True)
        est = est.sort_values("estacion")
        fig = px.bar(est, x="estacion", y="pedidos", color="estacion",
                     color_discrete_sequence=COLORS,
                     labels={"estacion": "", "pedidos": "Pedidos"})
        fig.update_layout(showlegend=False)
        styled_fig(fig, "Pedidos por Estacion")
        st.plotly_chart(fig, width='stretch')

with col2:
    if "temporada" in filtered.columns:
        tmp = filtered.groupby("temporada", as_index=False).agg(
            pedidos=("pedidos_totales", "sum"), kg=("kg_totales", "sum"),
            ars=("venta_total", "sum"), usd=("venta_total_usd", "sum"),
        )
        tmp_order = ["Alta", "Media", "Baja"]
        tmp["temporada"] = pd.Categorical(tmp["temporada"], categories=tmp_order, ordered=True)
        tmp = tmp.sort_values("temporada")
        fig = px.bar(tmp, x="temporada", y="pedidos", color="temporada",
                     color_discrete_sequence=COLORS,
                     labels={"temporada": "", "pedidos": "Pedidos"})
        fig.update_layout(showlegend=False)
        styled_fig(fig, "Pedidos por Temporada")
        st.plotly_chart(fig, width='stretch')


# -- AI Chat --
ai_chat_section(filtered, "ventas", "Ventas diarias: pedidos, KG, ingresos ARS/USD, estacion, clima")
