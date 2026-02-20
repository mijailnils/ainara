# ════════════════════════════════════════════════════════════════════════════
# Reusable dashboard components
# ════════════════════════════════════════════════════════════════════════════
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from theme import styled_fig, COLORS, TEAL, DARK_BLUE


# ── Date slicer ──────────────────────────────────────────────────────────────

DEFAULT_START = datetime.date(2023, 1, 1)
DEFAULT_END = datetime.date(2025, 12, 31)


def sidebar_date_slicer(key_prefix="global"):
    """Render a date range slider in the sidebar. Returns (start_date, end_date)."""
    st.sidebar.markdown("### Periodo")
    start, end = st.sidebar.slider(
        "Rango de fechas",
        min_value=DEFAULT_START,
        max_value=DEFAULT_END,
        value=(DEFAULT_START, DEFAULT_END),
        format="DD/MM/YY",
        key=f"{key_prefix}_slider",
    )
    st.sidebar.markdown("---")
    return start, end


def filter_by_date(df, date_col, start_date, end_date):
    """Filter a DataFrame by date range."""
    dates = pd.to_datetime(df[date_col])
    mask = (dates.dt.date >= start_date) & (dates.dt.date <= end_date)
    return df[mask].copy()


# ── Formatters ───────────────────────────────────────────────────────────────

def fmt_ars(val):
    """Format number as ARS currency."""
    if val is None or val == 0:
        return "$0"
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"${val/1_000:,.1f}K"
    return f"${val:,.0f}"


def fmt_usd(val):
    """Format number as USD."""
    if val is None or val == 0:
        return "U$D 0"
    if abs(val) >= 1_000_000:
        return f"U$D {val/1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"U$D {val/1_000:,.1f}K"
    return f"U$D {val:,.0f}"


def fmt_pct(val):
    """Format as percentage."""
    if val is None:
        return "—"
    return f"{val:.1f}%"


def kpi_row(metrics: list):
    """Render a row of KPI metrics. Each item: (label, value, delta=None)."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        label = m[0]
        value = m[1]
        delta = m[2] if len(m) > 2 else None
        col.metric(label, value, delta)


def line_chart(df, x, y, title=None, color=None):
    """Standard line chart."""
    fig = px.line(df, x=x, y=y, color=color)
    styled_fig(fig, title)
    st.plotly_chart(fig, width='stretch')


def bar_chart(df, x, y, title=None, color=None, horizontal=False):
    """Standard bar chart."""
    if horizontal:
        fig = px.bar(df, x=y, y=x, color=color, orientation='h')
    else:
        fig = px.bar(df, x=x, y=y, color=color)
    styled_fig(fig, title)
    st.plotly_chart(fig, width='stretch')


def pie_chart(df, names, values, title=None):
    """Standard pie chart."""
    fig = px.pie(df, names=names, values=values, color_discrete_sequence=COLORS)
    styled_fig(fig, title)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, width='stretch')
