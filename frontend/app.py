"""
Streamlit entry point.
Sets page config and renders the sidebar.
"""
import streamlit as st

st.set_page_config(
    page_title="AV/EV Consultant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("AV/EV Consultant")
st.sidebar.markdown("Expert guidance for autonomous and electric vehicles.")
st.sidebar.divider()
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("pages/1_chat.py",          label="Chat",            icon="💬")
st.sidebar.page_link("pages/2_policy_search.py", label="Policy search",   icon="📋")
st.sidebar.page_link("pages/3_dashboard.py",     label="Dashboards",      icon="📊")
st.sidebar.page_link("pages/4_upload_docs.py",   label="Upload documents",icon="📄")

st.title("Welcome to the AV/EV Consultant Assistant")
st.markdown("""
This AI-powered consultant answers technical and policy questions about:
- **Autonomous Vehicles** — SAE levels, sensor fusion, regulations, testing frameworks
- **Electric Vehicles** — battery chemistry, charging standards, market data, policy design

Use the sidebar to navigate to the chat or explore dashboards.
""")
