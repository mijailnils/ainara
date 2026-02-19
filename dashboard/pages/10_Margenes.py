import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_margenes
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Margenes - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Margenes")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_margenes()
df["mes"] = pd.to_datetime(df["mes"])

# ── Filter: dimension_tipo ───────────────────────────────────────────────────
dim_options = sorted(df["dimension_tipo"].dropna().unique())
sel_dim = st.selectbox(
    "Dimension",
    options=dim_options,
    index=dim_options.index("overall") if "overall" in dim_options else 0,
)

filtered = df[df["dimension_tipo"] == sel_dim].copy()
filtered = filtered.sort_values("mes")


# ── KPIs ──────────────────────────────────────────────────────────────────────
total_pedidos = int(filtered["pedidos"].sum()) if "pedidos" in filtered.columns else 0
total_kg = filtered["kg_totales"].sum() if "kg_totales" in filtered.columns else 0
total_contribucion = filtered["contribucion_mg"].sum() if "contribucion_mg" in filtered.columns else 0
total_contribucion_usd = filtered["contribucion_mg_usd"].sum() if "contribucion_mg_usd" in filtered.columns else 0

kpi_row([
    ("Pedidos (Q)", f"{total_pedidos:,}"),
    ("KG", f"{total_kg:,.0f}"),
    ("Contribucion MG ($)", fmt_ars(total_contribucion)),
    ("Contribucion MG (USD)", fmt_usd(total_contribucion_usd)),
])

st.divider()

# ── Line chart: margen_pct over time ─────────────────────────────────────────
st.subheader("Evolucion del Margen (%)")

color_col = "dimension_valor" if sel_dim != "overall" else None

fig_margin = px.line(
    filtered, x="mes", y="margen_pct",
    color=color_col,
    markers=True,
    labels={"mes": "Mes", "margen_pct": "Margen (%)", "dimension_valor": "Dimension"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_margin, "Margen % Mensual")
st.plotly_chart(fig_margin, use_container_width=True)

st.divider()

# ── Bar chart: contribucion_mg by month ──────────────────────────────────────
st.subheader("Contribucion Marginal por Mes")

fig_contrib = px.bar(
    filtered, x="mes", y="contribucion_mg",
    color=color_col,
    labels={"mes": "Mes", "contribucion_mg": "Contribucion MG ($)", "dimension_valor": "Dimension"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_contrib, "Contribucion Marginal Mensual")
st.plotly_chart(fig_contrib, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Margenes")

display_cols = [
    "mes", "dimension_tipo", "dimension_valor", "pedidos",
    "venta_total", "costo_total", "contribucion_mg", "margen_pct",
    "kg_totales", "venta_total_usd", "costo_total_usd", "contribucion_mg_usd",
]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values("mes", ascending=False),
    use_container_width=True,
    hide_index=True,
)
