import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from data import load_egresos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct, sidebar_date_slicer, filter_by_date
from ai_chat import ai_chat_section

apply_theme()
st.title("Egresos")

# ── Load & filter ─────────────────────────────────────────────────────────────
df = load_egresos()
df["mes"] = pd.to_datetime(df["mes"])
start_date, end_date = sidebar_date_slicer("egresos")
filtered = filter_by_date(df, "mes", start_date, end_date)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_monto = filtered["monto_total"].sum()
total_monto_usd = filtered["monto_total_usd"].sum() if "monto_total_usd" in filtered.columns else 0
total_cantidad = int(filtered["cantidad_egresos"].sum())

kpi_row([
    ("Total Egresos ($)", fmt_ars(total_monto)),
    ("Total Egresos (USD)", fmt_usd(total_monto_usd)),
    ("Cantidad de Egresos", f"{total_cantidad:,}"),
])

st.divider()

# ── Treemap: monto_total by categoria ─────────────────────────────────────────
st.subheader("Distribucion de Egresos por Categoria")

cat_totals = filtered.groupby("categoria", as_index=False)["monto_total"].sum()

fig_tree = px.treemap(
    cat_totals,
    path=["categoria"],
    values="monto_total",
    color="monto_total",
    color_continuous_scale=[[0, "#f5f5f5"], [0.5, TEAL], [1, DARK_BLUE]],
    labels={"monto_total": "Monto Total ($)", "categoria": "Categoria"},
)
styled_fig(fig_tree, "Egresos por Categoria")
fig_tree.update_layout(height=500)
st.plotly_chart(fig_tree, width='stretch')

st.divider()

# ── Monthly trend line by category (top 5) ────────────────────────────────────
st.subheader("Tendencia Mensual por Categoria (Top 5)")

top5_cats = cat_totals.nlargest(5, "monto_total")["categoria"].tolist()
trend_df = filtered[filtered["categoria"].isin(top5_cats)].copy()
trend_df = trend_df.sort_values("mes")

fig_trend = px.line(
    trend_df, x="mes", y="monto_total", color="categoria",
    markers=True,
    labels={"mes": "Mes", "monto_total": "Monto ($)", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_trend, "Tendencia Mensual - Top 5 Categorias")
st.plotly_chart(fig_trend, width='stretch')

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Egresos")

display_cols = [
    "mes", "anio", "categoria", "monto_total", "cantidad_egresos",
    "monto_total_usd", "var_interanual_pct",
]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values("mes", ascending=False),
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(df, "egresos", "Egresos mensuales por categoria: insumos, MO, servicios")
