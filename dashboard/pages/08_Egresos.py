import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_egresos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Egresos - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Egresos")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_egresos()
df["mes"] = pd.to_datetime(df["mes"])

# ── Year filter ───────────────────────────────────────────────────────────────
years = sorted(df["anio"].dropna().unique())
sel_year = st.selectbox("Ano", options=["Todos"] + [int(y) for y in years], index=0)

if sel_year != "Todos":
    filtered = df[df["anio"] == sel_year].copy()
else:
    filtered = df.copy()

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
st.plotly_chart(fig_tree, use_container_width=True)

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
st.plotly_chart(fig_trend, use_container_width=True)

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
    use_container_width=True,
    hide_index=True,
)
