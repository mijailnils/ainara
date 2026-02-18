import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app import load_clientes_nuevos
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, SAGE_GREEN
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct

st.set_page_config(page_title="Clientes Nuevos - Ainara", page_icon="\U0001f366", layout="wide")
apply_theme()
st.title("Clientes Nuevos")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_clientes_nuevos()
df["mes"] = pd.to_datetime(df["mes"])
df = df.sort_values("mes")

# ── Line chart: clientes_nuevos over time ─────────────────────────────────────
st.subheader("Adquisicion de Clientes Nuevos")

fig_nuevos = px.line(
    df, x="mes", y="clientes_nuevos",
    markers=True,
    labels={"mes": "Mes", "clientes_nuevos": "Clientes Nuevos"},
)
styled_fig(fig_nuevos, "Clientes Nuevos por Mes")
st.plotly_chart(fig_nuevos, use_container_width=True)

st.divider()

# ── Bar chart: retention rates ───────────────────────────────────────────────
st.subheader("Tasas de Retencion")

ret_cols = ["retencion_30d_pct", "retencion_60d_pct", "retencion_90d_pct"]
available_ret = [c for c in ret_cols if c in df.columns]

if available_ret:
    ret_df = df[["mes"] + available_ret].copy()
    ret_melted = ret_df.melt(
        id_vars="mes",
        value_vars=available_ret,
        var_name="Periodo",
        value_name="Retencion (%)",
    )
    ret_melted["Periodo"] = ret_melted["Periodo"].map({
        "retencion_30d_pct": "30 dias",
        "retencion_60d_pct": "60 dias",
        "retencion_90d_pct": "90 dias",
    })

    fig_ret = px.bar(
        ret_melted, x="mes", y="Retencion (%)", color="Periodo",
        barmode="group",
        labels={"mes": "Mes", "Retencion (%)": "Retencion (%)"},
        color_discrete_sequence=[TEAL, DARK_BLUE, SAGE_GREEN],
    )
    styled_fig(fig_ret, "Retencion por Cohorte")
    st.plotly_chart(fig_ret, use_container_width=True)

st.divider()

# ── Bar chart: channel breakdown ─────────────────────────────────────────────
st.subheader("Canal del Primer Pedido")

channel_cols = ["nuevos_delivery", "nuevos_local", "nuevos_mostrador"]
available_ch = [c for c in channel_cols if c in df.columns]

if available_ch:
    ch_df = df[["mes"] + available_ch].copy()
    ch_melted = ch_df.melt(
        id_vars="mes",
        value_vars=available_ch,
        var_name="Canal",
        value_name="Clientes",
    )
    ch_melted["Canal"] = ch_melted["Canal"].map({
        "nuevos_delivery": "Delivery",
        "nuevos_local": "Local",
        "nuevos_mostrador": "Mostrador",
    })

    fig_ch = px.bar(
        ch_melted, x="mes", y="Clientes", color="Canal",
        barmode="stack",
        labels={"mes": "Mes", "Clientes": "Clientes Nuevos"},
        color_discrete_sequence=COLORS,
    )
    styled_fig(fig_ch, "Clientes Nuevos por Canal")
    st.plotly_chart(fig_ch, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader("Tabla de Clientes Nuevos")

display_cols = [
    "mes", "clientes_nuevos", "nuevos_delivery", "nuevos_local", "nuevos_mostrador",
    "ticket_promedio_primer_pedido",
    "retencion_30d_pct", "retencion_60d_pct", "retencion_90d_pct",
    "var_vs_mes_anterior_pct",
]
available_cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[available_cols].sort_values("mes", ascending=False),
    use_container_width=True,
    hide_index=True,
)
