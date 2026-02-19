import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from app import load_rfm
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, SEGMENT_COLORS
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="RFM - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Analisis RFM")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_rfm()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_clientes = len(df)
total_pedidos = int(df["total_pedidos"].sum()) if "total_pedidos" in df.columns else 0
total_gastado = df["total_gastado"].sum() if "total_gastado" in df.columns else 0
total_gastado_usd = df["total_gastado_usd"].sum() if "total_gastado_usd" in df.columns else 0

kpi_row([
    ("Clientes (Q)", f"{total_clientes:,}"),
    ("Total Pedidos (Q)", f"{total_pedidos:,}"),
    ("Total Gastado ($)", fmt_ars(total_gastado)),
    ("Total Gastado (USD)", fmt_usd(total_gastado_usd)),
])

st.divider()

# ── Segment distribution bar chart ───────────────────────────────────────────
st.subheader("Distribucion por Segmento")

seg_counts = df["segmento_cliente"].value_counts().reset_index()
seg_counts.columns = ["Segmento", "Clientes"]

# Map colors
seg_color_map = {seg: SEGMENT_COLORS.get(seg, TEAL) for seg in seg_counts["Segmento"]}

fig_seg = px.bar(
    seg_counts.sort_values("Clientes", ascending=True),
    x="Clientes", y="Segmento", orientation="h",
    color="Segmento",
    color_discrete_map=seg_color_map,
    labels={"Clientes": "Cantidad", "Segmento": "Segmento"},
)
fig_seg.update_layout(showlegend=False)
styled_fig(fig_seg, "Clientes por Segmento RFM")
st.plotly_chart(fig_seg, use_container_width=True)

st.divider()

# ── Scatter plot: frecuencia vs monetario ─────────────────────────────────────
st.subheader("Frecuencia vs Monetario")

fig_scatter = px.scatter(
    df,
    x="frecuencia_score", y="monetario_score",
    color="segmento_cliente",
    size="total_gastado",
    size_max=20,
    color_discrete_map=seg_color_map,
    hover_data=["nombre", "total_pedidos", "total_gastado", "segmento_cliente"],
    labels={
        "frecuencia_score": "Score Frecuencia",
        "monetario_score": "Score Monetario",
        "segmento_cliente": "Segmento",
        "total_gastado": "Gasto Total",
    },
    opacity=0.7,
)
styled_fig(fig_scatter, "Frecuencia vs Monetario (tamano = gasto)")
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ── Data table with search ───────────────────────────────────────────────────
st.subheader("Tabla RFM")

search = st.text_input("Buscar cliente")

show = df.copy()
if search:
    show = show[
        show["nombre"].str.contains(search, case=False, na=False)
        | show["email"].str.contains(search, case=False, na=False)
    ]

display_cols = [
    "cliente_id", "nombre", "email", "segmento_cliente",
    "recencia_score", "frecuencia_score", "monetario_score", "rfm_total",
    "total_pedidos", "total_gastado", "total_gastado_usd", "ticket_promedio",
    "dias_desde_ultimo_pedido", "recencia_label", "frecuencia_label",
]
available_cols = [c for c in display_cols if c in show.columns]

st.dataframe(
    show[available_cols].sort_values("rfm_total", ascending=False),
    use_container_width=True,
    hide_index=True,
)
