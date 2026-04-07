"""
Multi-turn chat page with integrated data analyst.
When a question is data-oriented, shows a chart alongside the LLM answer.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import uuid
import re
import streamlit as st
import plotly.express as px
from core.data_analyst import run_data_query
from frontend.components.styles import inject_global_styles
from frontend.components.api_client import warmup, stream_with_retry, request_with_retry

st.title("AV/EV Consultant")
inject_global_styles()
st.markdown(
    """
    <div class="card">
        <strong>Ask anything about AV/EV policy, tech, or market data.</strong>
        <div class="tag">RAG</div>
        <div class="tag">Data Analysis</div>
        <div class="tag">Policy</div>
    </div>
    """,
    unsafe_allow_html=True,
)

API_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
warmup(API_URL)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Render history ─────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources", expanded=False):
                for s in msg["sources"]:
                    st.markdown(f"- `{s}`")
        if msg.get("chart") is not None:
            st.plotly_chart(msg["chart"], use_container_width=True)


# ── Chat input ─────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about AV/EV technology, policy, regulations, or market data..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # ── Step 1: Check if data query ────────────────────────────
        data_result = run_data_query(prompt)
        chart_fig   = None
        summary     = ""
        df          = None
        chart_type  = "bar"

        if data_result and data_result.get("dataframe") is not None:
            df         = data_result["dataframe"]
            summary    = data_result.get("summary", "")
            chart_type = data_result.get("chart_type", "bar")

        if df is not None and not df.empty and len(df.columns) >= 2:
            cols = df.columns.tolist()
            try:
                if chart_type == "none":
                    chart_fig = None
                elif chart_type == "pie":
                    chart_fig = px.pie(
                        df, names=cols[0], values=cols[1],
                        template='plotly_white',
                    )
                elif chart_type == "line":
                    chart_fig = px.line(
                        df, x=cols[0], y=cols[-1],
                        color=cols[1] if len(cols) > 2 else None,
                        template='plotly_white',
                    )
                else:
                    chart_fig = px.bar(
                        df, x=cols[0], y=cols[1],
                        template='plotly_white',
                        color_discrete_sequence=['#1D9E75'],
                    )
            except Exception:
                chart_fig = None

        if chart_fig:
            st.plotly_chart(chart_fig, use_container_width=True)

        # ── Step 2: Stream LLM answer ──────────────────────────────
        placeholder = st.empty()
        full_text   = ""
        sources     = []

        try:
            with stream_with_retry(
                "POST",
                f"{API_URL}/chat/stream",
                json={
                    "question": prompt,
                    "session_id": st.session_state.session_id,
                    "data_summary": summary if data_result else "",
                },
            ) as resp:
                for line in resp.iter_lines():
                    if line.startswith("__SOURCES__:"):
                        sources = [
                            s for s in line.replace("__SOURCES__:", "").split(",")
                            if s.strip()
                        ]
                    else:
                        full_text += line
                        full_text = (
                            full_text
                            .replace("###", "\n### ")
                            .replace("##", "\n## ")
                            .replace("#", "\n# ")
                        )
                        full_text = re.sub(r'([a-z])([A-Z][a-z])', r'\1\n\2', full_text)
                        placeholder.markdown(full_text + "▌")

            placeholder.markdown(full_text)

        except Exception as e:
            full_text = f"Could not reach API: {e}\n\n"
            if summary:
                full_text += f"**Data findings:**\n{summary}"
            placeholder.markdown(full_text)

        if sources:
            with st.expander("Document sources", expanded=False):
                for s in sources:
                    st.markdown(f"- `{s}`")

    st.session_state.messages.append({
        "role":    "assistant",
        "content": full_text,
        "sources": sources,
        "chart":   chart_fig,
    })


# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Try asking")
    examples = [
        "What are the top 10 countries for EV sales in 2023?",
        "What does SAE J3016 say about Level 4 autonomy?",
        "What is Nigeria's EV policy target according to the IEA?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": ex})
            st.rerun()

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        try:
            request_with_retry(
                "POST",
                f"{API_URL}/chat/clear",
                json={"session_id": st.session_state.session_id},
            )
        except Exception:
            pass
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.caption(f"Session: `{st.session_state.session_id[:8]}`")
