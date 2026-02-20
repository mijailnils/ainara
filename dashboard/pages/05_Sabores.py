import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from data import load_sabores
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct
from ai_chat import ai_chat_section

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
total_margen_usd = filtered["margen_total_usd"].sum() if "margen_total_usd" in filtered.columns else 0

kpi_row([
    ("Sabores", f"{total_sabores:,}"),
    ("Veces Pedido (Q)", f"{total_q:,}"),
    ("KG Vendidos", f"{total_kg:,.0f}"),
    ("Margen Total (USD)", fmt_usd(total_margen_usd)),
])

st.divider()

# ── Metric selector ──────────────────────────────────────────────────────────
metric_opts = {
    "Popularidad (Q)": "veces_pedido",
    "KG Vendidos": "kg_vendidos",
    "Margen Total (USD)": "margen_total_usd",
    "Margen/KG (USD)": "margen_estimado_por_kg_usd",
}
available_metrics = {k: v for k, v in metric_opts.items() if v in filtered.columns}
sel_metric = st.radio("Metrica", list(available_metrics.keys()), horizontal=True)
y_col = available_metrics[sel_metric]

# ── Horizontal bar: top 20 ────────────────────────────────────────────────────
st.subheader(f"Top 20 Sabores por {sel_metric}")

top20 = filtered.nlargest(20, y_col).sort_values(y_col)

fig = px.bar(
    top20, x=y_col, y="sabor", orientation="h",
    color="categoria",
    labels={y_col: sel_metric, "sabor": "Sabor", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig, f"Top 20 por {sel_metric}")
fig.update_layout(height=600)
st.plotly_chart(fig, width='stretch')

st.divider()

# ── Margen por KG: scatter ───────────────────────────────────────────────────
if "margen_estimado_por_kg_usd" in filtered.columns and "kg_vendidos" in filtered.columns:
    st.subheader("Margen/KG vs KG Vendidos")
    top50 = filtered.nlargest(50, "kg_vendidos")
    fig_scatter = px.scatter(
        top50, x="kg_vendidos", y="margen_estimado_por_kg_usd",
        size="veces_pedido", color="categoria",
        hover_name="sabor",
        labels={"kg_vendidos": "KG Vendidos", "margen_estimado_por_kg_usd": "Margen/KG (USD)", "categoria": "Categoria"},
        color_discrete_sequence=COLORS,
    )
    styled_fig(fig_scatter, "Margen por KG vs Volumen")
    st.plotly_chart(fig_scatter, width='stretch')

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
    st.plotly_chart(fig_heat, width='stretch')

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Sabores")

display_cols = [
    "ranking", "sabor", "categoria", "is_sin_azucar",
    "veces_pedido", "kg_vendidos", "costo_promedio_kg",
    "margen_estimado_por_kg", "margen_estimado_por_kg_usd",
    "margen_total_usd", "porcentaje_del_total", "estacion_top",
]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values("ranking"),
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(filtered, "sabores", "Sabores de helado: popularidad, KG, margen USD, estacionalidad")
