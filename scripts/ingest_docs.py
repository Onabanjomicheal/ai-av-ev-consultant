"""
One-shot document ingestion script.
Run: python scripts/ingest_docs.py
Reads all PDFs/HTML from data/raw_docs/ and builds the vector store.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

DOC_DIR     = Path("data/raw_docs")
PERSIST_DIR = Path("data/vectorstore")
CHUNK_SIZE  = 512
OVERLAP     = 64

LOADERS = {".pdf": PyPDFLoader, ".html": UnstructuredHTMLLoader, ".csv": CSVLoader}


def main():
    print(f"[ingest] Scanning {DOC_DIR} ...")
    docs = []
    files_ok = 0

    for root, _, files in os.walk(DOC_DIR):
        for fname in files:
            fpath = Path(root) / fname
            suffix = fpath.suffix.lower()
            if suffix not in LOADERS:
                continue
            try:
                loader = LOADERS[suffix](str(fpath))
                loaded = loader.load()
                category = Path(root).name
                for doc in loaded:
                    doc.metadata["source"] = fname
                    doc.metadata["category"] = category
                docs.extend(loaded)
                files_ok += 1
                print(f"  [ok] {fpath}")
            except Exception as e:
                print(f"  [skip] {fpath}: {e}")

    if not docs:
        print("[ingest] No documents found. Add PDFs to data/raw_docs/av/ or data/raw_docs/ev/")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=OVERLAP)
    chunks = splitter.split_documents(docs)
    print(f"[ingest] {files_ok} files → {len(chunks)} chunks")

    print("[ingest] Loading embedding model (first run downloads ~90 MB)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("[ingest] Building vector store...")
    Chroma.from_documents(chunks, embeddings, persist_directory=str(PERSIST_DIR))
    print(f"[ingest] Done. Vector store saved to {PERSIST_DIR}")


if __name__ == "__main__":
    main()
