"""
Streamlit entry point.
Sets page config and renders the sidebar.
"""
import os
import sys
import streamlit as st

# Ensure repo root is on sys.path when running: streamlit run frontend/app.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from frontend.components.styles import inject_global_styles

st.set_page_config(
    page_title="AV/EV Consultant",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_styles()

st.sidebar.title("AV/EV Consultant")
st.sidebar.markdown("Expert guidance for autonomous and electric vehicles.")
st.sidebar.divider()
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("pages/1_chat.py",          label="Chat")
st.sidebar.page_link("pages/2_policy_search.py", label="Policy search")
st.sidebar.page_link("pages/3_dashboard.py",     label="Dashboards")
st.sidebar.page_link("pages/4_upload_docs.py",   label="Upload documents")

st.markdown(
    """
    <div class="hero-grid">
        <div class="card">
            <h1>AV/EV Consultant Assistant</h1>
            <p>
                A focused AI copilot for autonomous and electric vehicle decisions:
                engineering guidance, policy analysis, and market intelligence.
            </p>
            <div>
                <span class="tag">Policy</span>
                <span class="tag">Engineering</span>
                <span class="tag">Market</span>
                <span class="tag">Safety</span>
            </div>
        </div>
        <div class="card">
            <h3>Quick Start</h3>
            <p>Use the sidebar to open chat, search regulations, or explore dashboards.</p>
            <p><strong>Tip:</strong> Ask a question like “What does SAE J3016 say about Level 4?”</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
