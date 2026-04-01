import streamlit as st


def render_source_card(source: str, snippet: str):
    with st.container(border=True):
        st.markdown(f"**{source}**")
        st.caption(snippet[:300] + "..." if len(snippet) > 300 else snippet)
