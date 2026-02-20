# ════════════════════════════════════════════════════════════════════════════
# Ainara Brand Theme — Colors, Fonts, CSS for Streamlit
# Corporate Tech Geometric + Ainara color system
# ════════════════════════════════════════════════════════════════════════════

# Colors
TEAL = "#5ec6c9"
TEAL_DARK = "#02777d"
TEAL_HOVER = "#4cbdc1"
DARK_BLUE = "#467999"
DARK_BLUE_LIGHT = "#478cb8"
SAGE_GREEN = "#6a961f"
CHARCOAL = "#3a3a3a"
CHARCOAL_LIGHT = "#5a5a5a"
LIGHT_GRAY = "#f5f5f5"
WHITE = "#ffffff"
RED = "#e74c3c"
ORANGE = "#f39c12"

# Plotly color sequence
COLORS = [TEAL, DARK_BLUE, SAGE_GREEN, TEAL_DARK, DARK_BLUE_LIGHT,
          CHARCOAL_LIGHT, "#e8a87c", "#d5c4a1", "#85dcba", ORANGE]

# Segment colors (for RFM)
SEGMENT_COLORS = {
    "VIP": TEAL_DARK,
    "Leal": TEAL,
    "Potencial": DARK_BLUE_LIGHT,
    "Nuevo": SAGE_GREEN,
    "Ocasional": CHARCOAL_LIGHT,
    "En riesgo": ORANGE,
    "Dormido": "#d5c4a1",
    "Perdido": RED,
    "Sin compras": LIGHT_GRAY,
}

# ── SVG geometric background ─────────────────────────────────────────────────
# Abstract geometric: subtle lines + interconnected nodes
# Slate blue palette, low contrast, corporate tech
_GEO_BG_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>
<defs>
  <pattern id='geo' x='0' y='0' width='200' height='200' patternUnits='userSpaceOnUse'>
    <!-- Grid lines -->
    <line x1='0' y1='100' x2='200' y2='100' stroke='rgba(70,121,153,0.06)' stroke-width='0.5'/>
    <line x1='100' y1='0' x2='100' y2='200' stroke='rgba(70,121,153,0.06)' stroke-width='0.5'/>
    <line x1='0' y1='0' x2='200' y2='200' stroke='rgba(70,121,153,0.04)' stroke-width='0.5'/>
    <line x1='200' y1='0' x2='0' y2='200' stroke='rgba(70,121,153,0.04)' stroke-width='0.5'/>
    <!-- Cross lines -->
    <line x1='50' y1='0' x2='150' y2='200' stroke='rgba(94,198,201,0.035)' stroke-width='0.5'/>
    <line x1='150' y1='0' x2='50' y2='200' stroke='rgba(94,198,201,0.035)' stroke-width='0.5'/>
    <line x1='0' y1='50' x2='200' y2='150' stroke='rgba(70,121,153,0.03)' stroke-width='0.5'/>
    <!-- Nodes -->
    <circle cx='100' cy='100' r='2' fill='rgba(70,121,153,0.08)'/>
    <circle cx='0' cy='0' r='1.5' fill='rgba(94,198,201,0.07)'/>
    <circle cx='200' cy='0' r='1.5' fill='rgba(94,198,201,0.07)'/>
    <circle cx='0' cy='200' r='1.5' fill='rgba(94,198,201,0.07)'/>
    <circle cx='200' cy='200' r='1.5' fill='rgba(94,198,201,0.07)'/>
    <circle cx='50' cy='50' r='1' fill='rgba(70,121,153,0.06)'/>
    <circle cx='150' cy='50' r='1' fill='rgba(70,121,153,0.06)'/>
    <circle cx='50' cy='150' r='1' fill='rgba(70,121,153,0.06)'/>
    <circle cx='150' cy='150' r='1' fill='rgba(70,121,153,0.06)'/>
    <!-- Connecting segments -->
    <line x1='50' y1='50' x2='100' y2='100' stroke='rgba(94,198,201,0.05)' stroke-width='0.5'/>
    <line x1='150' y1='50' x2='100' y2='100' stroke='rgba(94,198,201,0.05)' stroke-width='0.5'/>
    <line x1='50' y1='150' x2='100' y2='100' stroke='rgba(94,198,201,0.05)' stroke-width='0.5'/>
    <line x1='150' y1='150' x2='100' y2='100' stroke='rgba(94,198,201,0.05)' stroke-width='0.5'/>
  </pattern>
</defs>
<rect width='800' height='600' fill='url(%23geo)'/>
</svg>"""

_GEO_BG_ENCODED = _GEO_BG_SVG.replace('\n', '').replace("'", "%27").replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace(" ", "%20")

# Sidebar SVG: complementary subtle pattern
_SIDEBAR_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='300' height='400'>
<defs>
  <pattern id='sbgeo' x='0' y='0' width='120' height='120' patternUnits='userSpaceOnUse'>
    <line x1='0' y1='60' x2='120' y2='60' stroke='rgba(2,119,125,0.06)' stroke-width='0.5'/>
    <line x1='60' y1='0' x2='60' y2='120' stroke='rgba(2,119,125,0.06)' stroke-width='0.5'/>
    <line x1='0' y1='0' x2='120' y2='120' stroke='rgba(2,119,125,0.04)' stroke-width='0.5'/>
    <line x1='120' y1='0' x2='0' y2='120' stroke='rgba(2,119,125,0.04)' stroke-width='0.5'/>
    <circle cx='60' cy='60' r='1.5' fill='rgba(2,119,125,0.08)'/>
    <circle cx='0' cy='0' r='1' fill='rgba(94,198,201,0.06)'/>
    <circle cx='120' cy='0' r='1' fill='rgba(94,198,201,0.06)'/>
    <circle cx='0' cy='120' r='1' fill='rgba(94,198,201,0.06)'/>
    <circle cx='120' cy='120' r='1' fill='rgba(94,198,201,0.06)'/>
    <line x1='0' y1='0' x2='60' y2='60' stroke='rgba(2,119,125,0.04)' stroke-width='0.3'/>
    <line x1='120' y1='0' x2='60' y2='60' stroke='rgba(2,119,125,0.04)' stroke-width='0.3'/>
  </pattern>
</defs>
<rect width='300' height='400' fill='url(%23sbgeo)'/>
</svg>"""

_SIDEBAR_BG_ENCODED = _SIDEBAR_SVG.replace('\n', '').replace("'", "%27").replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace(" ", "%20")

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxygen:wght@400;700&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Lato', sans-serif;
    color: #3a3a3a;
}}

/* ── Main content area: geometric background ──────────────── */
[data-testid="stAppViewContainer"] {{
    background-color: #f0f3f5;
    background-image: url("data:image/svg+xml,{_GEO_BG_ENCODED}");
    background-repeat: repeat;
    background-size: 400px 300px;
}}

[data-testid="stMain"] > div {{
    background: transparent;
}}

h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    font-family: 'Oxygen', sans-serif !important;
    font-weight: 700;
    color: #467999;
}}

/* ── Sidebar: geometric tech ──────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: #eaf0f2;
    background-image: url("data:image/svg+xml,{_SIDEBAR_BG_ENCODED}");
    background-repeat: repeat;
    background-size: 240px 240px;
    border-right: 2px solid #d0dfe5;
}}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    color: #02777d;
    font-family: 'Oxygen', sans-serif !important;
    letter-spacing: 0.3px;
}}

/* Sidebar nav links */
[data-testid="stSidebar"] .stPageLink a,
[data-testid="stSidebar"] nav a {{
    font-family: 'Lato', sans-serif;
    font-weight: 600;
    color: #3a3a3a;
    padding: 8px 12px;
    border-radius: 8px;
    transition: all 0.2s ease;
}}

[data-testid="stSidebar"] .stPageLink a:hover,
[data-testid="stSidebar"] nav a:hover {{
    background-color: rgba(94,198,201,0.18);
    color: #02777d;
}}

[data-testid="stSidebar"] hr {{
    border-color: rgba(2,119,125,0.15);
    margin: 12px 0;
}}

/* ── KPI Metrics ──────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background-color: #ffffff;
    border: 1px solid #d8e2e8;
    border-left: 4px solid #5ec6c9;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(70,121,153,0.08);
}}

[data-testid="stMetricValue"] {{
    font-family: 'Oxygen', sans-serif;
    font-weight: 700;
    color: #02777d;
}}

[data-testid="stMetricLabel"] {{
    font-family: 'Lato', sans-serif;
    color: #5a5a5a;
}}

/* ── Buttons ──────────────────────────────────────────────── */
.stButton > button {{
    border-radius: 24px;
    background-color: #5ec6c9;
    color: white;
    border: none;
    padding: 8px 24px;
    font-family: 'Lato', sans-serif;
    font-weight: 700;
    transition: background-color 0.2s;
}}
.stButton > button:hover {{
    background-color: #467999;
    color: white;
}}

/* ── Tabs ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab"] {{
    font-family: 'Lato', sans-serif;
    font-weight: 700;
}}
.stTabs [aria-selected="true"] {{
    border-bottom-color: #5ec6c9;
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
}}

hr {{
    border-color: rgba(94,198,201,0.25);
}}

/* ── Chart containers: white card with border ─────────────── */
[data-testid="stPlotlyChart"] {{
    background-color: #ffffff;
    border: 1px solid #d8e2e8;
    border-radius: 10px;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(70,121,153,0.06);
    overflow: hidden;
}}

/* ── Dataframe styling ────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    background-color: #ffffff;
    border: 1px solid #d8e2e8;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(70,121,153,0.06);
    overflow: hidden;
}}

/* ── Captions ─────────────────────────────────────────────── */
.stCaption {{
    color: #7a8a8a;
    font-size: 0.85rem;
}}

/* ── Slider styling ──────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] {{
    background-color: #5ec6c9;
}}
</style>
"""


def apply_theme():
    """Inject Ainara CSS into Streamlit."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def styled_fig(fig, title=None):
    """Apply Ainara styling to a Plotly figure."""
    fig.update_layout(
        font=dict(family="Lato, sans-serif", color=CHARCOAL, size=13),
        title=dict(
            text=title,
            font=dict(family="Oxygen, sans-serif", size=18, color=DARK_BLUE),
            x=0.02, xanchor="left",
        ) if title else None,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        colorway=COLORS,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            font_size=12,
            font_family="Lato, sans-serif",
            bordercolor="#d8e2e8",
        ),
        margin=dict(l=50, r=30, t=55 if title else 25, b=45),
        legend=dict(
            font=dict(size=12, family="Lato, sans-serif"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#d8e2e8",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
    )
    fig.update_xaxes(
        gridcolor="#eef2f2",
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=11, color=CHARCOAL_LIGHT),
        title_font=dict(size=12, color=CHARCOAL),
    )
    fig.update_yaxes(
        gridcolor="#eef2f2",
        gridwidth=1,
        zeroline=False,
        tickfont=dict(size=11, color=CHARCOAL_LIGHT),
        title_font=dict(size=12, color=CHARCOAL),
        tickformat=",.0f",
    )
    return fig
