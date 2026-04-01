import streamlit as st


def render_message(role: str, content: str, sources: list[str] | None = None):
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    else:
        with st.chat_message("assistant"):
            st.markdown(content)
            if sources:
                with st.expander("Sources", expanded=False):
                    for src in sources:
                        st.markdown(f"- `{src}`")
