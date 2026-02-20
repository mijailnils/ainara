import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import streamlit as st
from data import load_rfm
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, SEGMENT_COLORS
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct
from ai_chat import ai_chat_section

apply_theme()
st.title("Analisis RFM")
st.caption("R = Recencia (dias desde ultimo pedido) | F = Frecuencia (pedidos/semana) | M = Volumen (KG comprados)")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_rfm()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_clientes = len(df)
total_pedidos = int(df["total_pedidos"].sum()) if "total_pedidos" in df.columns else 0
total_kg = df["kg_total"].sum() if "kg_total" in df.columns else 0
total_gastado_usd = df["total_gastado_usd"].sum() if "total_gastado_usd" in df.columns else 0

kpi_row([
    ("Clientes (Q)", f"{total_clientes:,}"),
    ("Total Pedidos (Q)", f"{total_pedidos:,}"),
    ("KG Total", f"{total_kg:,.0f}"),
    ("Total Gastado (USD)", fmt_usd(total_gastado_usd)),
])

st.divider()

# ── Segment distribution bar chart ───────────────────────────────────────────
st.subheader("Distribucion por Segmento")

seg_counts = df["segmento_cliente"].value_counts().reset_index()
seg_counts.columns = ["Segmento", "Clientes"]

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
st.plotly_chart(fig_seg, width='stretch')

st.divider()

# ── Scatter plot: frecuencia vs volumen (KG) ─────────────────────────────────
st.subheader("Frecuencia vs Volumen (KG)")

fig_scatter = px.scatter(
    df,
    x="frecuencia_score", y="monetario_score",
    color="segmento_cliente",
    size="kg_total",
    size_max=20,
    color_discrete_map=seg_color_map,
    hover_data=["nombre", "total_pedidos", "kg_total", "segmento_cliente"],
    labels={
        "frecuencia_score": "Score Frecuencia",
        "monetario_score": "Score Volumen (KG)",
        "segmento_cliente": "Segmento",
        "kg_total": "KG Total",
    },
    opacity=0.7,
)
styled_fig(fig_scatter, "Frecuencia vs Volumen KG (tamano = kg)")
st.plotly_chart(fig_scatter, width='stretch')

st.divider()

# ── Data table with search ───────────────────────────────────────────────────
st.subheader("Tabla RFM")

search = st.text_input("Buscar cliente")

show = df.copy()
if search:
    show = show[
        show["nombre"].str.contains(search, case=False, na=False)
    ]

display_cols = [
    "cliente_id", "nombre", "segmento_cliente",
    "recencia_score", "frecuencia_score", "monetario_score", "rfm_total",
    "total_pedidos", "kg_total", "total_gastado", "total_gastado_usd", "ticket_promedio",
    "dias_desde_ultimo_pedido", "recencia_label", "frecuencia_label",
]
available_cols = [c for c in display_cols if c in show.columns]

st.dataframe(
    show[available_cols].sort_values("rfm_total", ascending=False),
    width='stretch',
    hide_index=True,
)


# -- AI Chat --
ai_chat_section(df, "rfm", "Analisis RFM: recencia, frecuencia, volumen KG, segmentos")
