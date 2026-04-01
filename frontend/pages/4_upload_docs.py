"""
Document upload and ingestion trigger page.
"""
import os
import httpx
import streamlit as st

st.title("Upload AV/EV Documents")
st.markdown("Upload PDFs or HTML files to expand the knowledge base.")

API_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

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
                timeout=300,
            )
            data = resp.json()
            st.success(
                f"Done! {data['files_processed']} files → {data['chunks_created']} chunks created."
            )
        except Exception as e:
            st.error(f"Ingestion failed: {e}")
