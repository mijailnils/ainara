import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from data import load_margenes
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct, sidebar_date_slicer, filter_by_date
from ai_chat import ai_chat_section

apply_theme()
st.title("Margenes")

# ── Load & filter ─────────────────────────────────────────────────────────────
df = load_margenes()
df["mes"] = pd.to_datetime(df["mes"])
start_date, end_date = sidebar_date_slicer("margenes")
df = filter_by_date(df, "mes", start_date, end_date)

# ── Sidebar: dimension filter ────────────────────────────────────────────────
dim_options = sorted(df["dimension_tipo"].dropna().unique())
sel_dim = st.sidebar.selectbox(
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
st.plotly_chart(fig_margin, width='stretch')

st.divider()

# ── Bar chart: contribucion_mg by month (ARS / USD toggle) ──────────────────
st.subheader("Contribucion Marginal por Mes")

tab_ars, tab_usd = st.tabs(["$ ARS", "U$D"])

with tab_ars:
    fig_contrib = px.bar(
        filtered, x="mes", y="contribucion_mg",
        color=color_col,
        labels={"mes": "Mes", "contribucion_mg": "Contribucion MG ($)", "dimension_valor": "Dimension"},
        color_discrete_sequence=COLORS,
    )
    styled_fig(fig_contrib, "Contribucion Marginal (ARS)")
    st.plotly_chart(fig_contrib, width='stretch')

with tab_usd:
    if "contribucion_mg_usd" in filtered.columns:
        fig_contrib_usd = px.bar(
            filtered, x="mes", y="contribucion_mg_usd",
            color=color_col,
            labels={"mes": "Mes", "contribucion_mg_usd": "Contribucion MG (USD)", "dimension_valor": "Dimension"},
            color_discrete_sequence=COLORS,
        )
        styled_fig(fig_contrib_usd, "Contribucion Marginal (USD)")
        st.plotly_chart(fig_contrib_usd, width='stretch')
    else:
        st.info("No hay datos en USD disponibles.")

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
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(filtered, "margenes", "Margenes mensuales: overall, por tipo retiro, por tipo pago ARS/USD")
