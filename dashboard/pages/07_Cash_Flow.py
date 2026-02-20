import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data import load_cash_flow
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, RED, SAGE_GREEN
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct, sidebar_date_slicer, filter_by_date
from ai_chat import ai_chat_section

apply_theme()
st.title("Flujo de Caja")

st.caption(
    "Inflows = cobros reales (efectivo + MP neto de comision + transferencias). "
    "Outflows = todos los egresos registrados (insumos, MO, servicios, etc.) + delivery. "
    "A diferencia del PnL, el Cash Flow mide dinero real que entra y sale. "
    "Inflows < Ingresos PnL porque: (1) MP ya tiene comision descontada, "
    "(2) ventas plataforma son estimadas en PnL."
)

# ── Load & filter ─────────────────────────────────────────────────────────────
df = load_cash_flow()
df["mes"] = pd.to_datetime(df["mes"])
start_date, end_date = sidebar_date_slicer("cashflow")
df = filter_by_date(df, "mes", start_date, end_date)
df = df.sort_values("mes")

df["acumulado_periodo"] = df["flujo_neto"].cumsum()
if "flujo_neto_usd" in df.columns:
    df["acumulado_periodo_usd"] = df["flujo_neto_usd"].cumsum()

if df.empty:
    st.warning("No hay datos para el periodo seleccionado.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_inflows = float(df["total_inflows"].sum())
total_outflows = float(df["total_outflows"].sum())
total_flujo_neto = float(df["flujo_neto"].sum())
total_flujo_neto_usd = float(df["flujo_neto_usd"].sum()) if "flujo_neto_usd" in df.columns else 0

kpi_row([
    ("Total Inflows ($)", fmt_ars(total_inflows)),
    ("Total Outflows ($)", fmt_ars(total_outflows)),
    ("Flujo Neto ($)", fmt_ars(total_flujo_neto)),
    ("Flujo Neto (USD)", fmt_usd(total_flujo_neto_usd)),
])

st.divider()

# ── Composicion de Inflows y Outflows ────────────────────────────────────────
st.subheader("Composicion")

c1, c2 = st.columns(2)
with c1:
    inflow_comp = pd.DataFrame({
        "Fuente": ["Efectivo", "MP Neto", "Transferencia"],
        "Monto": [
            float(df["cobros_efectivo"].sum()),
            float(df["cobros_mp_neto"].sum()),
            float(df["cobros_transferencia"].sum()),
        ]
    })
    fig_in = px.pie(inflow_comp, names="Fuente", values="Monto",
                    color_discrete_sequence=[TEAL, DARK_BLUE, SAGE_GREEN])
    fig_in.update_traces(textposition="inside", textinfo="percent+label")
    styled_fig(fig_in, "Inflows: de donde entra el dinero")
    st.plotly_chart(fig_in, width='stretch')

with c2:
    outflow_comp = pd.DataFrame({
        "Tipo": ["Egresos Efectivo", "Egresos Tarjeta", "Egresos MP", "Egresos Otro", "Delivery"],
        "Monto": [
            float(df["egresos_efectivo"].sum()),
            float(df["egresos_tarjeta"].sum()),
            float(df["egresos_mp"].sum()),
            float(df["egresos_otro"].sum()),
            float(df["costo_delivery"].sum()),
        ]
    })
    outflow_comp = outflow_comp[outflow_comp["Monto"] > 0]
    fig_out = px.pie(outflow_comp, names="Tipo", values="Monto",
                     color_discrete_sequence=COLORS)
    fig_out.update_traces(textposition="inside", textinfo="percent+label")
    styled_fig(fig_out, "Outflows: a donde sale el dinero")
    st.plotly_chart(fig_out, width='stretch')

st.divider()

# ── Monthly bars: ARS / USD tabs ─────────────────────────────────────────────
st.subheader("Inflows vs Outflows Mensuales")

tab_ars, tab_usd = st.tabs(["$ ARS", "U$D"])

with tab_ars:
    fig_cf = go.Figure()
    fig_cf.add_bar(x=df["mes"], y=df["total_inflows"].astype(float), name="Inflows", marker_color=TEAL)
    fig_cf.add_bar(x=df["mes"], y=-df["total_outflows"].astype(float), name="Outflows", marker_color=RED)
    styled_fig(fig_cf, "Flujo de Caja Mensual (ARS)")
    fig_cf.update_layout(barmode="relative", yaxis_title="Monto ($)")
    st.plotly_chart(fig_cf, width='stretch')

with tab_usd:
    if "total_inflows_usd" in df.columns:
        fig_cf_usd = go.Figure()
        fig_cf_usd.add_bar(x=df["mes"], y=df["total_inflows_usd"].astype(float), name="Inflows USD", marker_color=TEAL)
        fig_cf_usd.add_bar(x=df["mes"], y=-df["total_outflows_usd"].astype(float), name="Outflows USD", marker_color=RED)
        styled_fig(fig_cf_usd, "Flujo de Caja Mensual (USD)")
        fig_cf_usd.update_layout(barmode="relative", yaxis_title="Monto (USD)")
        st.plotly_chart(fig_cf_usd, width='stretch')

st.divider()

# ── Acumulado: ARS / USD tabs ────────────────────────────────────────────────
st.subheader("Flujo Neto Acumulado (del periodo)")
st.caption("Acumulado calculado desde el inicio del periodo seleccionado")

tab_a_ars, tab_a_usd = st.tabs(["$ ARS", "U$D"])

with tab_a_ars:
    fig_acum = px.line(df, x="mes", y="acumulado_periodo", markers=True,
                       labels={"mes": "Mes", "acumulado_periodo": "Acumulado ($)"})
    styled_fig(fig_acum, "Acumulado ARS")
    st.plotly_chart(fig_acum, width='stretch')

with tab_a_usd:
    if "acumulado_periodo_usd" in df.columns:
        fig_acum_usd = px.line(df, x="mes", y="acumulado_periodo_usd", markers=True,
                               labels={"mes": "Mes", "acumulado_periodo_usd": "Acumulado (USD)"})
        styled_fig(fig_acum_usd, "Acumulado USD")
        st.plotly_chart(fig_acum_usd, width='stretch')

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Cash Flow")

display_cols = [
    "mes", "cobros_efectivo", "cobros_mp_neto", "cobros_transferencia",
    "total_inflows", "egresos_efectivo", "egresos_tarjeta", "costo_delivery",
    "total_outflows", "flujo_neto", "acumulado_periodo",
    "total_inflows_usd", "total_outflows_usd", "flujo_neto_usd",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("mes", ascending=False),
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(df, "cashflow", "Flujo de caja mensual: inflows, outflows, flujo neto ARS/USD")
