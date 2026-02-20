# ════════════════════════════════════════════════════════════════════════════
# AI Chart Builder — Claude-powered custom chart generation
# ════════════════════════════════════════════════════════════════════════════
import os
import re
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from theme import styled_fig, COLORS, TEAL, DARK_BLUE, SAGE_GREEN, RED, ORANGE, TEAL_DARK, WHITE

# Load .env file at import time
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().strip().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _get_api_key():
    """Get Anthropic API key from st.secrets, env, or sidebar fallback."""
    # 1. st.secrets (Streamlit Cloud)
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    # 2. Environment variable (.env local)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        key = st.session_state.get("_anthropic_key", "")
    if not key:
        with st.sidebar:
            st.markdown("---")
            key = st.text_input(
                "Anthropic API Key",
                type="password",
                key="_sidebar_api_key",
                help="Ingresa tu ANTHROPIC_API_KEY para habilitar el chatbot",
            )
            if key:
                st.session_state["_anthropic_key"] = key
    return key


def _df_context(df: pd.DataFrame, name: str) -> str:
    """Build a concise description of a DataFrame for the LLM."""
    lines = [f"DataFrame: `{name}`", f"Shape: {df.shape[0]} rows x {df.shape[1]} columns", ""]
    lines.append("Columns (name → dtype):")
    for col in df.columns:
        dtype = df[col].dtype
        nunique = df[col].nunique()
        sample_vals = ""
        if nunique <= 10 and dtype == "object":
            vals = df[col].dropna().unique()[:8]
            sample_vals = f" — values: {list(vals)}"
        elif pd.api.types.is_numeric_dtype(df[col]):
            vmin = df[col].min()
            vmax = df[col].max()
            sample_vals = f" — range: [{vmin}, {vmax}]"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            vmin = df[col].min()
            vmax = df[col].max()
            sample_vals = f" — range: [{vmin}, {vmax}]"
        lines.append(f"  - {col}: {dtype} (nunique={nunique}){sample_vals}")
    lines.append(f"\nFirst 3 rows:\n{df.head(3).to_string()}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are an analytics assistant for Ainara Helados (ice cream shop in Buenos Aires).
You help create custom Plotly charts from the available data.

RULES:
1. Return ONLY a Python code block that creates a Plotly figure assigned to variable `fig`.
2. The DataFrame is available as `df`. Do NOT load or read any files.
3. Use plotly.express (as `px`) or plotly.graph_objects (as `go`).
4. Apply the theme: call `styled_fig(fig, "Title")` at the end.
5. Available theme constants: COLORS, TEAL, DARK_BLUE, SAGE_GREEN, RED, ORANGE, TEAL_DARK, WHITE
6. Do NOT use st.plotly_chart — just create `fig`, the system will render it.
7. You can do pandas operations on `df` (filtering, groupby, pivot, etc).
8. Keep code concise. No imports needed — px, go, pd, styled_fig, and color constants are available.
9. If the user asks for a table or data summary, create a simple bar/line chart instead.
10. Respond in the same language as the user (Spanish if they write in Spanish).
11. Before the code block, write a brief 1-line description of the chart.
"""


def _call_claude(messages: list, df_context: str, api_key: str) -> str:
    """Call Claude API and return the response text."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    system = SYSTEM_PROMPT + "\n\nAvailable data:\n" + df_context

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _extract_code(text: str) -> str:
    """Extract Python code from a response (code block or raw)."""
    pattern = r"```(?:python)?\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _execute_chart(code: str, df: pd.DataFrame):
    """Execute chart code and return the figure."""
    namespace = {
        "df": df,
        "pd": pd,
        "px": px,
        "go": go,
        "styled_fig": styled_fig,
        "COLORS": COLORS,
        "TEAL": TEAL,
        "DARK_BLUE": DARK_BLUE,
        "SAGE_GREEN": SAGE_GREEN,
        "RED": RED,
        "ORANGE": ORANGE,
        "TEAL_DARK": TEAL_DARK,
        "WHITE": WHITE,
    }
    exec(code, namespace)
    return namespace.get("fig")


_SCIENTIST_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="38" height="38">
  <circle cx="32" cy="20" r="12" fill="#467999"/>
  <circle cx="32" cy="20" r="10" fill="#e8f4f5"/>
  <circle cx="28" cy="18" r="2" fill="#467999"/>
  <circle cx="36" cy="18" r="2" fill="#467999"/>
  <path d="M28 23 Q32 27 36 23" stroke="#467999" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <rect x="24" y="8" width="3" height="6" rx="1.5" fill="#467999" transform="rotate(-15 25.5 11)"/>
  <rect x="37" y="8" width="3" height="6" rx="1.5" fill="#467999" transform="rotate(15 38.5 11)"/>
  <rect x="30" y="5" width="4" height="7" rx="2" fill="#467999"/>
  <circle cx="23" cy="20" r="4" fill="none" stroke="#5ec6c9" stroke-width="1.5"/>
  <line x1="20" y1="23" x2="18" y2="25" stroke="#5ec6c9" stroke-width="1.5"/>
  <path d="M24 32 L22 50 Q22 54 26 54 L38 54 Q42 54 42 50 L40 32Z" fill="#02777d"/>
  <path d="M28 42 L26 54" stroke="#5ec6c9" stroke-width="1" opacity="0.5"/>
  <path d="M36 42 L38 54" stroke="#5ec6c9" stroke-width="1" opacity="0.5"/>
  <circle cx="32" cy="40" r="2" fill="#5ec6c9" opacity="0.7"/>
  <path d="M40 36 L48 32 L50 38 L44 40Z" fill="#5ec6c9"/>
  <circle cx="49" cy="31" r="3" fill="none" stroke="#5ec6c9" stroke-width="1.2"/>
  <circle cx="49" cy="31" r="1" fill="#e74c3c" opacity="0.6"/>
</svg>"""


def ai_chat_section(df: pd.DataFrame, page_key: str, page_description: str = ""):
    """Render an AI chat section for custom chart generation."""
    st.divider()

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'{_SCIENTIST_SVG}'
        f'<div>'
        f'<h3 style="margin:0;font-family:Oxygen,sans-serif;color:#467999;">Asistente AI</h3>'
        f'<p style="margin:0;font-size:13px;color:#7a8a8a;">Pregunta lo que quieras sobre los datos. Claude creara graficos personalizados.</p>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    api_key = _get_api_key()
    if not api_key:
        st.info("Configura tu ANTHROPIC_API_KEY para usar el asistente AI.")
        return

    # Session state for chat history
    history_key = f"_ai_chat_{page_key}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    # Display chat history
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(msg.get("text", ""))
                if msg.get("fig"):
                    st.plotly_chart(msg["fig"], width='stretch')
                if msg.get("error"):
                    st.error(msg["error"])
            else:
                st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Ej: Mostra un grafico de barras con ventas por estacion", key=f"_chat_input_{page_key}")

    if prompt:
        # Add user message
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build context
        context = _df_context(df, page_key)
        if page_description:
            context = f"Page: {page_description}\n\n{context}"

        # Build messages for Claude (include last 6 exchanges for context)
        claude_messages = []
        for msg in st.session_state[history_key][-7:]:
            if msg["role"] == "user":
                claude_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                claude_messages.append({"role": "assistant", "content": msg.get("raw_response", msg.get("text", ""))})

        # Call Claude
        with st.chat_message("assistant"):
            with st.spinner("Generando grafico..."):
                try:
                    raw_response = _call_claude(claude_messages, context, api_key)
                    code = _extract_code(raw_response)

                    # Extract text before code block
                    text_before = raw_response.split("```")[0].strip()
                    if text_before:
                        st.markdown(text_before)

                    if code:
                        fig = _execute_chart(code, df)
                        if fig:
                            st.plotly_chart(fig, width='stretch')
                            st.session_state[history_key].append({
                                "role": "assistant",
                                "text": text_before,
                                "fig": fig,
                                "raw_response": raw_response,
                            })
                        else:
                            st.warning("El codigo no genero un grafico (variable `fig` no encontrada).")
                            st.session_state[history_key].append({
                                "role": "assistant",
                                "text": text_before,
                                "error": "No se genero grafico",
                                "raw_response": raw_response,
                            })
                    else:
                        st.markdown(raw_response)
                        st.session_state[history_key].append({
                            "role": "assistant",
                            "text": raw_response,
                            "raw_response": raw_response,
                        })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state[history_key].append({
                        "role": "assistant",
                        "text": "",
                        "error": error_msg,
                        "raw_response": error_msg,
                    })

        st.rerun()
