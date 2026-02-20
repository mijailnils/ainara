import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data import load_pnl
from theme import apply_theme, styled_fig, COLORS, TEAL, DARK_BLUE, SAGE_GREEN, RED, ORANGE, TEAL_DARK
from components import kpi_row, fmt_ars, fmt_usd, fmt_pct, sidebar_date_slicer, filter_by_date
from ai_chat import ai_chat_section

apply_theme()
st.title("Estado de Resultados (PnL)")

st.caption(
    "Ingresos = venta bruta (sistema + plataforma). "
    "Insumos = compras reales de ingredientes y potes (egresos). "
    "Resultado = Ingresos - Insumos - Gastos Op. - Comisiones - Delivery. "
    "COGS sistema es informativo (costo teorico por receta del sistema de pedidos)."
)

# ── Load & filter ─────────────────────────────────────────────────────────────
df = load_pnl()
df["mes"] = pd.to_datetime(df["mes"])
start_date, end_date = sidebar_date_slicer("pnl")
df = filter_by_date(df, "mes", start_date, end_date)
df = df.sort_values("mes")

if df.empty:
    st.warning("No hay datos para el periodo seleccionado.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_ingresos = df["ingresos_totales"].sum()
total_insumos = df["gasto_insumos"].sum()
total_resultado = df["resultado_operativo"].sum()
total_resultado_usd = df["resultado_operativo_usd"].sum() if "resultado_operativo_usd" in df.columns else 0

kpi_row([
    ("Ingresos ($)", fmt_ars(total_ingresos)),
    ("Insumos ($)", fmt_ars(total_insumos)),
    ("Resultado ($)", fmt_ars(total_resultado)),
    ("Resultado (USD)", fmt_usd(total_resultado_usd)),
])

st.divider()

# ── Waterfall chart: latest month ─────────────────────────────────────────────
st.subheader("Waterfall - Ultimo Mes")

latest = df.iloc[-1]

waterfall_items = [
    ("Ingresos", latest["ingresos_totales"]),
    ("Insumos", -latest["gasto_insumos"]),
    ("Gastos Op.", -latest["total_gastos_operativos"]),
    ("Comisiones", -latest["total_comisiones"]),
    ("Delivery", -latest["costo_delivery"]),
]

labels = [item[0] for item in waterfall_items] + ["Resultado"]
values = [item[1] for item in waterfall_items] + [latest["resultado_operativo"]]
measures = ["relative"] * len(waterfall_items) + ["total"]

fig_wf = go.Figure(go.Waterfall(
    name="PnL",
    orientation="v",
    measure=measures,
    x=labels,
    y=values,
    connector={"line": {"color": "#d8e2e8"}},
    increasing={"marker": {"color": TEAL}},
    decreasing={"marker": {"color": RED}},
    totals={"marker": {"color": DARK_BLUE}},
    textposition="outside",
    text=[fmt_ars(abs(v)) for v in values],
))
styled_fig(fig_wf, f"PnL - {latest['mes'].strftime('%B %Y')}")
fig_wf.update_layout(showlegend=False)
st.plotly_chart(fig_wf, width='stretch')

st.divider()

# ── Monthly trend: ARS / USD tabs ────────────────────────────────────────────
st.subheader("Tendencia Mensual")

tab_ars, tab_usd = st.tabs(["$ ARS", "U$D"])

with tab_ars:
    fig_trend = go.Figure()
    fig_trend.add_scatter(x=df["mes"], y=df["ingresos_totales"], name="Ingresos", mode="lines+markers")
    fig_trend.add_scatter(x=df["mes"], y=df["gasto_insumos"], name="Insumos", mode="lines+markers")
    fig_trend.add_scatter(x=df["mes"], y=df["resultado_operativo"], name="Resultado", mode="lines+markers")
    styled_fig(fig_trend, "Ingresos vs Insumos vs Resultado (ARS)")
    st.plotly_chart(fig_trend, width='stretch')

with tab_usd:
    usd_cols = ["ingresos_totales_usd", "gasto_insumos_usd", "resultado_operativo_usd"]
    if all(c in df.columns for c in usd_cols):
        fig_trend_usd = go.Figure()
        fig_trend_usd.add_scatter(x=df["mes"], y=df["ingresos_totales_usd"], name="Ingresos", mode="lines+markers")
        fig_trend_usd.add_scatter(x=df["mes"], y=df["gasto_insumos_usd"], name="Insumos", mode="lines+markers")
        fig_trend_usd.add_scatter(x=df["mes"], y=df["resultado_operativo_usd"], name="Resultado", mode="lines+markers")
        styled_fig(fig_trend_usd, "Ingresos vs Insumos vs Resultado (USD)")
        st.plotly_chart(fig_trend_usd, width='stretch')

st.divider()

# ── Tabla PnL Mensual Estilizada ─────────────────────────────────────────────
st.subheader("Tabla PnL Mensual")

tab_tbl_ars, tab_tbl_usd = st.tabs(["$ ARS", "U$D"])

# Define rows for ARS and USD
pnl_rows_ars = {
    "Ingresos": "ingresos_totales",
    "Insumos (compra real)": "gasto_insumos",
    "Margen Bruto": "margen_bruto",
    "Margen Bruto %": "margen_bruto_pct",
    "Gastos Operativos": "total_gastos_operativos",
    "  Mano de Obra": "gasto_mano_obra",
    "  Alquiler": "gasto_alquiler",
    "  Servicios": "gasto_servicios",
    "  Marketing": "gasto_marketing",
    "  Impuestos": "gasto_impuestos",
    "  Logistica": "gasto_logistica",
    "  Otros": "gasto_otros",
    "Comisiones": "total_comisiones",
    "Delivery": "costo_delivery",
    "Resultado Operativo": "resultado_operativo",
    "Resultado Op. %": "resultado_operativo_pct",
    "COGS Sistema (ref.)": "cogs_total",
    "Pedidos (Q)": "pedidos_totales",
    "KG": "kg_totales",
}

pnl_rows_usd = {
    "Ingresos": "ingresos_totales_usd",
    "Insumos (compra real)": "gasto_insumos_usd",
    "Margen Bruto": "margen_bruto_usd",
    "Margen Bruto %": "margen_bruto_pct",
    "Gastos Operativos": "total_gastos_operativos_usd",
    "Resultado Operativo": "resultado_operativo_usd",
    "Resultado Op. %": "resultado_operativo_pct",
    "COGS Sistema (ref.)": "cogs_total_usd",
    "Tipo Cambio": "tipo_cambio_promedio",
    "Pedidos (Q)": "pedidos_totales",
    "KG": "kg_totales",
}


def _build_pnl_html(rows_def, sorted_df, month_labels, currency="ars"):
    """Build a styled HTML table for PnL."""
    fmt = fmt_ars if currency == "ars" else fmt_usd

    # Row styling rules
    highlight_rows = {"Ingresos", "Margen Bruto", "Resultado Operativo"}
    pct_rows = {"Margen Bruto %", "Resultado Op. %"}
    count_rows = {"Pedidos (Q)", "KG", "Tipo Cambio"}
    indent_rows = {"  Mano de Obra", "  Alquiler", "  Servicios",
                   "  Marketing", "  Impuestos", "  Logistica", "  Otros"}

    # Find max values for bar sizing
    max_val = 1
    for label, col in rows_def.items():
        if col in sorted_df.columns and label not in pct_rows and label not in count_rows:
            vals = sorted_df[col].dropna().abs()
            if len(vals) > 0:
                max_val = max(max_val, vals.max())

    html = '<div style="overflow-x:auto;">'
    html += '<table style="width:100%;border-collapse:collapse;font-family:Lato,sans-serif;font-size:13px;">'

    # Header
    html += '<thead><tr>'
    html += '<th style="text-align:left;padding:10px 12px;background:#467999;color:white;font-family:Oxygen,sans-serif;font-weight:700;border-radius:6px 0 0 0;min-width:180px;">Concepto</th>'
    for i, m in enumerate(month_labels):
        radius = "0 6px 0 0" if i == len(month_labels) - 1 else "0"
        html += f'<th style="text-align:right;padding:10px 12px;background:#467999;color:white;font-family:Oxygen,sans-serif;font-weight:600;border-radius:{radius};min-width:100px;">{m}</th>'
    html += '</tr></thead><tbody>'

    for label, col in rows_def.items():
        if col not in sorted_df.columns:
            continue
        vals = sorted_df[col].tolist()

        # Determine row style
        is_highlight = label in highlight_rows
        is_resultado = label == "Resultado Operativo"
        is_margen = label == "Margen Bruto"
        is_pct = label in pct_rows
        is_count = label in count_rows
        is_indent = label in indent_rows

        # Row background
        if is_resultado:
            row_bg = "#e8f4f5"
            label_color = "#02777d"
            font_weight = "700"
        elif is_margen:
            row_bg = "#f0f8f0"
            label_color = "#467999"
            font_weight = "700"
        elif is_highlight:
            row_bg = "#f5f9fc"
            label_color = "#467999"
            font_weight = "700"
        elif is_indent:
            row_bg = "#fafafa"
            label_color = "#7a8a8a"
            font_weight = "400"
        else:
            row_bg = "white"
            label_color = "#3a3a3a"
            font_weight = "500"

        html += f'<tr style="background:{row_bg};border-bottom:1px solid #eef2f5;">'
        display_label = label if not is_indent else label
        html += f'<td style="padding:8px 12px;color:{label_color};font-weight:{font_weight};white-space:nowrap;">{display_label}</td>'

        for v in vals:
            if pd.isna(v):
                html += '<td style="text-align:right;padding:8px 12px;color:#ccc;">-</td>'
                continue

            if is_pct:
                cell_text = f"{v:.1f}%"
                # Color based on value
                if v > 0:
                    cell_color = "#02777d"
                elif v < 0:
                    cell_color = "#e74c3c"
                else:
                    cell_color = "#3a3a3a"
                html += f'<td style="text-align:right;padding:8px 12px;color:{cell_color};font-weight:600;">{cell_text}</td>'
            elif is_count:
                if col == "tipo_cambio_promedio":
                    cell_text = f"${v:,.0f}"
                elif col == "kg_totales":
                    cell_text = f"{v:,.0f}"
                else:
                    cell_text = f"{int(v):,}"
                html += f'<td style="text-align:right;padding:8px 12px;color:#5a5a5a;">{cell_text}</td>'
            else:
                cell_text = fmt(v)
                # Bar background for monetary values
                if is_resultado or is_margen:
                    bar_pct = min(abs(v) / max_val * 100, 100) if max_val > 0 else 0
                    if v >= 0:
                        bar_color = "rgba(94,198,201,0.2)" if is_resultado else "rgba(106,150,31,0.15)"
                    else:
                        bar_color = "rgba(231,76,60,0.15)"
                    cell_color = "#02777d" if v >= 0 else "#e74c3c"
                    html += f'<td style="text-align:right;padding:8px 12px;color:{cell_color};font-weight:700;background:linear-gradient(90deg,{bar_color} {bar_pct:.0f}%,transparent {bar_pct:.0f}%);">{cell_text}</td>'
                elif is_highlight:
                    html += f'<td style="text-align:right;padding:8px 12px;color:#467999;font-weight:600;">{cell_text}</td>'
                else:
                    html += f'<td style="text-align:right;padding:8px 12px;color:#3a3a3a;">{cell_text}</td>'

        html += '</tr>'

    html += '</tbody></table></div>'
    return html


sorted_df = df.sort_values("mes")
month_labels = sorted_df["mes"].dt.strftime("%m-%y").tolist()

with tab_tbl_ars:
    html_ars = _build_pnl_html(pnl_rows_ars, sorted_df, month_labels, "ars")
    st.markdown(html_ars, unsafe_allow_html=True)

with tab_tbl_usd:
    html_usd = _build_pnl_html(pnl_rows_usd, sorted_df, month_labels, "usd")
    st.markdown(html_usd, unsafe_allow_html=True)


# -- AI Chat --
ai_chat_section(df, "pnl", "Estado de resultados mensual: ingresos, insumos, gastos, resultado ARS/USD")
