import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_pedidos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Pedidos - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Explorador de Pedidos")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_pedidos()
df["fecha"] = pd.to_datetime(df["fecha"])

# ── Filters ───────────────────────────────────────────────────────────────────
st.sidebar.header("Filtros")

min_date = df["fecha"].min().date()
max_date = df["fecha"].max().date()

start_date = st.sidebar.date_input("Desde", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Hasta", value=max_date, min_value=min_date, max_value=max_date)

tipo_retiro_opts = sorted(df["tipo_retiro"].dropna().unique())
tipo_retiro = st.sidebar.multiselect("Tipo de retiro", tipo_retiro_opts, default=tipo_retiro_opts)

tipo_pago_opts = sorted(df["tipo_pago"].dropna().unique())
tipo_pago = st.sidebar.multiselect("Tipo de pago", tipo_pago_opts, default=tipo_pago_opts)

estado_opts = sorted(df["estado_nombre"].dropna().unique())
estados = st.sidebar.multiselect("Estado", estado_opts, default=estado_opts)

mask = (
    (df["fecha"].dt.date >= start_date)
    & (df["fecha"].dt.date <= end_date)
    & (df["tipo_retiro"].isin(tipo_retiro))
    & (df["tipo_pago"].isin(tipo_pago))
    & (df["estado_nombre"].isin(estados))
)
filtered = df[mask].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_pedidos = len(filtered)
total_ventas = filtered["total"].sum()
ticket_prom = filtered["total"].mean() if total_pedidos > 0 else 0
clientes_unicos = filtered["cliente_id"].nunique()

kpi_row([
    ("Pedidos", f"{total_pedidos:,}"),
    ("Ventas", fmt_ars(total_ventas)),
    ("Ticket Promedio", fmt_ars(ticket_prom)),
    ("Clientes Unicos", f"{clientes_unicos:,}"),
])

st.divider()

# ── Bar chart: pedidos by hora ────────────────────────────────────────────────
st.subheader("Pedidos por Hora del Dia")

hour_counts = filtered["hora"].value_counts().sort_index().reset_index()
hour_counts.columns = ["Hora", "Pedidos"]

fig_hour = px.bar(
    hour_counts, x="Hora", y="Pedidos",
    labels={"Hora": "Hora del dia", "Pedidos": "Cantidad de pedidos"},
    color_discrete_sequence=[TEAL],
)
styled_fig(fig_hour, "Distribucion por Hora")
st.plotly_chart(fig_hour, use_container_width=True)

st.divider()

# ── Bar chart: pedidos by horario ─────────────────────────────────────────────
st.subheader("Pedidos por Franja Horaria")

if "horario" in filtered.columns:
    horario_counts = filtered["horario"].value_counts().reset_index()
    horario_counts.columns = ["Horario", "Pedidos"]
    horario_order = ["Mediodia", "Tarde", "Noche", "Trasnoche", "Otro"]
    horario_counts["Horario"] = pd.Categorical(
        horario_counts["Horario"], categories=horario_order, ordered=True
    )
    horario_counts = horario_counts.sort_values("Horario")

    fig_horario = px.bar(
        horario_counts, x="Horario", y="Pedidos",
        color="Horario", color_discrete_sequence=COLORS,
        labels={"Horario": "Franja Horaria", "Pedidos": "Pedidos"},
    )
    fig_horario.update_layout(showlegend=False)
    styled_fig(fig_horario, "Pedidos por Franja Horaria")
    st.plotly_chart(fig_horario, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Pedidos")

show_cols = [
    "pedido_id", "fecha", "cliente_nombre", "barrio", "tipo_retiro",
    "tipo_pago", "subtotal", "descuento", "costo_envio", "total",
    "estado_nombre", "hora", "horario", "cantidad_productos",
]
available_cols = [c for c in show_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values("fecha", ascending=False),
    use_container_width=True,
    hide_index=True,
)
