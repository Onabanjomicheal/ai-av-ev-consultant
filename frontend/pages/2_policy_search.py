"""
Policy and regulation search page.
Performs semantic search over the ingested document corpus.
"""
import httpx
import streamlit as st
from frontend.components.source_card import render_source_card

st.title("Policy & Regulation Search")
st.markdown("Search across ingested AV and EV policy documents semantically.")

API_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

query = st.text_input("Search query", placeholder="EV charging infrastructure mandates EU 2030...")
k = st.slider("Number of results", min_value=1, max_value=10, value=5)

if st.button("Search") and query:
    with st.spinner("Searching..."):
        try:
            resp = httpx.get(f"{API_URL}/search", params={"q": query, "k": k}, timeout=30)
            results = resp.json().get("results", [])
            if not results:
                st.info("No results found. Make sure documents are ingested.")
            for r in results:
                render_source_card(r["source"], r["content"])
        except Exception as e:
            st.error(f"Search failed: {e}")
