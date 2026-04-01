"""
Multi-turn chat page.
Streams responses from the FastAPI backend.
"""
import uuid
import httpx
import streamlit as st
from frontend.components.chat_bubble import render_message

st.title("Chat with the AV/EV Consultant")

API_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render history
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], msg.get("sources"))

# Input
if prompt := st.chat_input("Ask about AV or EV technology, regulations, or policy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_message("user", prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        sources = []

        try:
            with httpx.Client(timeout=120) as client:
                with client.stream(
                    "POST",
                    f"{API_URL}/chat/stream",
                    json={"question": prompt, "session_id": st.session_state.session_id},
                ) as resp:
                    for line in resp.iter_lines():
                        if line.startswith("__SOURCES__:"):
                            sources = line.replace("__SOURCES__:", "").split(",")
                        else:
                            full_text += line
                            placeholder.markdown(full_text + "▌")

            placeholder.markdown(full_text)

            if sources:
                with st.expander("Sources", expanded=False):
                    for s in sources:
                        st.markdown(f"- `{s}`")

        except Exception as e:
            full_text = f"Error contacting API: {e}"
            placeholder.error(full_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text,
        "sources": sources,
    })

# Sidebar controls
with st.sidebar:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        try:
            httpx.post(
                f"{API_URL}/chat/clear",
                json={"session_id": st.session_state.session_id},
            )
        except Exception:
            pass
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    st.caption(f"Session: `{st.session_state.session_id[:8]}`")
