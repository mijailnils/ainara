import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from data import load_productos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct
from ai_chat import ai_chat_section

apply_theme()
st.title("Productos")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_productos()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_products = len(df)
total_vendido = int(df["veces_vendido"].sum())
total_kg = df["kg_vendidos"].sum() if "kg_vendidos" in df.columns else 0
total_ingreso = df["ingreso_estimado"].sum() if "ingreso_estimado" in df.columns else 0
total_ingreso_usd = df["ingreso_estimado_usd"].sum() if "ingreso_estimado_usd" in df.columns else 0
total_margen = df["margen_estimado"].sum() if "margen_estimado" in df.columns else 0

kpi_row([
    ("Unidades Vendidas (Q)", f"{total_vendido:,}"),
    ("KG Vendidos", f"{total_kg:,.0f}"),
    ("Ingreso Estimado ($)", fmt_ars(total_ingreso)),
    ("Ingreso (USD)", fmt_usd(total_ingreso_usd)),
])

st.divider()

# ── Metric selector ──────────────────────────────────────────────────────────
metric_opts = {"Unidades (Q)": "veces_vendido", "KG": "kg_vendidos", "Ingreso ($)": "ingreso_estimado", "Ingreso (USD)": "ingreso_estimado_usd", "Margen ($)": "margen_estimado"}
available_metrics = {k: v for k, v in metric_opts.items() if v in df.columns}
sel_metric = st.radio("Metrica", list(available_metrics.keys()), horizontal=True)
y_col = available_metrics[sel_metric]

# ── Horizontal bar chart: top 20 ──────────────────────────────────────────────
st.subheader(f"Top 20 Productos por {sel_metric}")

top20 = df.nlargest(20, y_col).sort_values(y_col)

fig = px.bar(
    top20, x=y_col, y="producto", orientation="h",
    color="categoria",
    labels={y_col: sel_metric, "producto": "Producto", "categoria": "Categoria"},
    color_discrete_sequence=COLORS,
)
styled_fig(fig, f"Top 20 por {sel_metric}")
fig.update_layout(height=600)
st.plotly_chart(fig, width='stretch')

st.divider()

# ── Margen % por categoria ───────────────────────────────────────────────────
if "margen_pct" in df.columns:
    st.subheader("Margen % por Categoria")
    cat_margin = df.groupby("categoria", as_index=False).agg(
        margen_pct_prom=("margen_pct", "mean"),
        kg_vendidos=("kg_vendidos", "sum"),
        ingreso=("ingreso_estimado", "sum"),
    ).sort_values("margen_pct_prom", ascending=True)

    fig_mg = px.bar(
        cat_margin, x="margen_pct_prom", y="categoria", orientation="h",
        labels={"margen_pct_prom": "Margen %", "categoria": ""},
        color_discrete_sequence=[TEAL],
    )
    styled_fig(fig_mg, "Margen Promedio por Categoria")
    st.plotly_chart(fig_mg, width='stretch')

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Productos")

display_cols = [
    "ranking", "producto", "categoria", "precio_base", "peso_kg",
    "veces_vendido", "kg_vendidos", "ingreso_estimado",
    "ingreso_estimado_usd", "margen_estimado", "margen_pct",
    "porcentaje_del_total",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("ranking"),
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(df, "productos", "Productos vendidos: unidades, KG, ingreso, margen")
