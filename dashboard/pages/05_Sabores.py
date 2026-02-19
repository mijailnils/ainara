import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_sabores
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Sabores - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Sabores")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_sabores()

# ── Toggle: sin azucar filter ─────────────────────────────────────────────────
sin_azucar_opt = st.radio(
    "Filtro sin azucar", ["Todos", "Solo sin azucar", "Solo con azucar"],
    horizontal=True,
)

filtered = df.copy()
if sin_azucar_opt == "Solo sin azucar":
    filtered = filtered[filtered["is_sin_azucar"] == 1]
elif sin_azucar_opt == "Solo con azucar":
    filtered = filtered[filtered["is_sin_azucar"] == 0]

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_sabores = len(filtered)
total_q = int(filtered["veces_pedido"].sum())
total_kg = filtered["kg_vendidos"].sum() if "kg_vendidos" in filtered.columns else 0

kpi_row([
    ("Sabores", f"{total_sabores:,}"),
    ("Veces Pedido (Q)", f"{total_q:,}"),
    ("KG Vendidos", f"{total_kg:,.0f}"),
])

st.divider()

# ── Horizontal bar: veces_pedido top 20 ──────────────────────────────────────
st.subheader("Top 20 Sabores por Popularidad")

top20_pop = filtered.nlargest(20, "veces_pedido").sort_values("veces_pedido")

fig_pop = px.bar(
    top20_pop, x="veces_pedido", y="sabor", orientation="h",
    color="categoria",
    labels={"veces_pedido": "Veces Pedido", "sabor": "Sabor", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_pop, "Top 20 Sabores por Popularidad")
fig_pop.update_layout(height=600)
st.plotly_chart(fig_pop, use_container_width=True)

st.divider()

# ── Horizontal bar: kg_vendidos top 20 ───────────────────────────────────────
st.subheader("Top 20 Sabores por KG Vendidos")

top20_kg = filtered.nlargest(20, "kg_vendidos").sort_values("kg_vendidos")

fig_kg = px.bar(
    top20_kg, x="kg_vendidos", y="sabor", orientation="h",
    color="categoria",
    labels={"kg_vendidos": "KG Vendidos", "sabor": "Sabor", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig_kg, "Top 20 Sabores por KG")
fig_kg.update_layout(height=600)
st.plotly_chart(fig_kg, use_container_width=True)

st.divider()

# ── Seasonality heatmap ──────────────────────────────────────────────────────
st.subheader("Estacionalidad de los Top 15 Sabores")

top15 = filtered.nlargest(15, "veces_pedido").copy()

season_cols = ["pct_verano", "pct_otono", "pct_invierno", "pct_primavera"]
available_season = [c for c in season_cols if c in top15.columns]

if available_season:
    heatmap_df = top15.set_index("sabor")[available_season]
    heatmap_df.columns = [c.replace("pct_", "").capitalize() for c in available_season]

    fig_heat = px.imshow(
        heatmap_df.values,
        x=heatmap_df.columns.tolist(),
        y=heatmap_df.index.tolist(),
        color_continuous_scale=[[0, "#f5f5f5"], [0.5, TEAL], [1, DARK_BLUE]],
        aspect="auto",
        text_auto=".1f",
        labels={"color": "% Pedidos"},
    )
    styled_fig(fig_heat, "Estacionalidad (%)")
    fig_heat.update_layout(height=500)
    st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Sabores")

display_cols = [
    "ranking", "sabor", "categoria", "is_sin_azucar",
    "veces_pedido", "pedidos_distintos", "kg_vendidos",
    "porcentaje_del_total", "estacion_top",
]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values("ranking"),
    use_container_width=True,
    hide_index=True,
)
