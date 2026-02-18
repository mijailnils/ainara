# ════════════════════════════════════════════════════════════════════════════
# Ainara Brand Theme — Colors, Fonts, CSS for Streamlit
# Based on ainara.com.ar design system
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

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oxygen:wght@400;700&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
    color: #3a3a3a;
}

h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Oxygen', sans-serif !important;
    font-weight: 700;
    color: #467999;
}

[data-testid="stSidebar"] {
    background-color: #f5f5f5;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 {
    color: #02777d;
}

[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-left: 4px solid #5ec6c9;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

[data-testid="stMetricValue"] {
    font-family: 'Oxygen', sans-serif;
    font-weight: 700;
    color: #02777d;
}

[data-testid="stMetricLabel"] {
    font-family: 'Lato', sans-serif;
    color: #5a5a5a;
}

.stButton > button {
    border-radius: 24px;
    background-color: #5ec6c9;
    color: white;
    border: none;
    padding: 8px 24px;
    font-family: 'Lato', sans-serif;
    font-weight: 700;
    transition: background-color 0.2s;
}
.stButton > button:hover {
    background-color: #467999;
    color: white;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Lato', sans-serif;
    font-weight: 700;
}
.stTabs [aria-selected="true"] {
    border-bottom-color: #5ec6c9;
}

hr {
    border-color: rgba(94,198,201,0.25);
}
</style>
"""


def apply_theme():
    """Inject Ainara CSS into Streamlit."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def styled_fig(fig, title=None):
    """Apply Ainara styling to a Plotly figure."""
    fig.update_layout(
        font=dict(family="Lato, sans-serif", color=CHARCOAL),
        title=dict(
            text=title,
            font=dict(family="Oxygen, sans-serif", size=18, color=DARK_BLUE)
        ) if title else None,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        colorway=COLORS,
        hovermode="x unified",
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        legend=dict(font=dict(size=11)),
    )
    fig.update_xaxes(gridcolor="#f0f0f0", zeroline=False)
    fig.update_yaxes(gridcolor="#f0f0f0", zeroline=False)
    return fig
