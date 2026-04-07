"""
Document upload and ingestion trigger page.
"""
import os
import streamlit as st
from frontend.components.styles import inject_global_styles
import httpx

st.title("Upload AV/EV Documents")
st.markdown("Upload PDFs or HTML files to expand the knowledge base.")
inject_global_styles()
st.markdown(
    """
    <div class="card">
        <strong>Keep the knowledge base current with your latest reports.</strong>
        <div class="tag">Ingestion</div>
        <div class="tag">RAG Index</div>
        <div class="tag">Sources</div>
    </div>
    """,
    unsafe_allow_html=True,
)

API_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

category = st.selectbox("Document category", ["av", "ev"])
uploaded = st.file_uploader("Choose files", type=["pdf", "html", "csv"], accept_multiple_files=True)

if uploaded and st.button("Upload and ingest"):
    save_dir = f"data/raw_docs/{category}"
    os.makedirs(save_dir, exist_ok=True)

    for f in uploaded:
        path = os.path.join(save_dir, f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())

    with st.spinner("Ingesting documents into vector store..."):
        try:
            resp = httpx.post(
                f"{API_URL}/ingest",
                json={"directory": save_dir},
                timeout=600,
            )
            data = resp.json()
            st.success(
                f"Done! {data['files_processed']} files → {data['chunks_created']} chunks created."
            )
        except Exception as e:
            st.error(f"Ingestion failed: {e}")
