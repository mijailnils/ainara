import os
import sys

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DASHBOARD_DIR, "..", "ainara.duckdb")
if DASHBOARD_DIR not in sys.path:
    sys.path.insert(0, DASHBOARD_DIR)

from theme import apply_theme, styled_fig, TEAL, DARK_BLUE
from components import kpi_row, fmt_ars, fmt_usd

# ── Data loaders ──────────────────────────────────────────────────────────────

def _conn():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(ttl=300)
def load_table(name: str) -> pd.DataFrame:
    conn = _conn()
    df = conn.execute(f'SELECT * FROM main."{name}"').df()
    conn.close()
    return df


def load_ventas():        return load_table("fct_ventas_diarias")
def load_pedidos():       return load_table("fct_pedidos")
def load_clientes():      return load_table("dim_clientes")
def load_productos():     return load_table("rpt_productos_vendidos")
def load_sabores():       return load_table("rpt_sabores")
def load_pnl():           return load_table("rpt_pnl")
def load_cash_flow():     return load_table("rpt_cash_flow")
def load_egresos():       return load_table("rpt_egresos")
def load_rfm():           return load_table("rpt_rfm")
def load_margenes():      return load_table("rpt_margenes")
def load_puntos():        return load_table("rpt_puntos")
def load_zonas():         return load_table("rpt_zonas")
def load_clientes_nuevos(): return load_table("rpt_clientes_nuevos")


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ainara Analytics",
    page_icon="🍦",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ── Header ────────────────────────────────────────────────────────────────────

st.title("Ainara Analytics")
st.caption("Dashboard analítico de Ainara Helados")

# ── Home KPIs ─────────────────────────────────────────────────────────────────

ventas = load_ventas()
clientes = load_clientes()

total_revenue = ventas["venta_total"].sum()
total_orders = ventas["pedidos_totales"].sum()
total_kg = ventas["kg_totales"].sum()
unique_customers = clientes[clientes["total_pedidos"] > 0].shape[0]

kpi_row([
    ("Ventas Totales", fmt_ars(total_revenue)),
    ("Pedidos Totales", f"{int(total_orders):,}"),
    ("KG Totales", f"{total_kg:,.0f} kg"),
    ("Clientes con compras", f"{unique_customers:,}"),
])

st.divider()

# ── Revenue trend ─────────────────────────────────────────────────────────────

ventas["mes_dt"] = pd.to_datetime(ventas["fecha"]).dt.to_period("M").dt.to_timestamp()
monthly = ventas.groupby("mes_dt", as_index=False).agg(
    venta=("venta_total", "sum"),
    pedidos=("pedidos_totales", "sum"),
)

fig = px.line(monthly, x="mes_dt", y="venta", markers=True,
              labels={"mes_dt": "Mes", "venta": "Ventas ($)"})
styled_fig(fig, "Ventas Mensuales")
st.plotly_chart(fig, use_container_width=True)

# ── Dataset info ──────────────────────────────────────────────────────────────

fecha_min = pd.to_datetime(ventas["fecha"]).min().strftime("%d/%m/%Y")
fecha_max = pd.to_datetime(ventas["fecha"]).max().strftime("%d/%m/%Y")

c1, c2 = st.columns(2)
c1.markdown(f"**Periodo:** {fecha_min} — {fecha_max}")
c2.markdown(f"**Fuente:** DuckDB (ainara.duckdb)")

st.divider()

st.markdown("""
**Secciones disponibles** — navegá desde el panel izquierdo:

| Seccion | Descripcion |
|---------|-------------|
| Ventas | Tendencia diaria, mix pagos, clima, USD |
| Clientes | Segmentación, preferencias, gasto |
| Pedidos | Explorer con filtros |
| Productos | Ranking de productos |
| Sabores | Ranking, estacionalidad, kg |
| PnL | Estado de Resultados mensual |
| Cash Flow | Flujo de caja |
| Egresos | Gastos por categoría |
| RFM | Análisis RFM detallado |
| Márgenes | Evolución de márgenes |
| Puntos | Programa de fidelidad |
| Zonas | Métricas de delivery |
| Clientes Nuevos | Adquisición y retención |
""")
