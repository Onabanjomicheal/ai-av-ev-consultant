import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from api.schemas.documents import IngestRequest, IngestResponse
from api.services.rag import RAGSettings

router = APIRouter(prefix="/ingest", tags=["ingest"])

LOADERS = {
    ".pdf":  PyPDFLoader,
    ".html": UnstructuredHTMLLoader,
    ".csv":  CSVLoader,
}


@router.post("", response_model=IngestResponse)
async def ingest_documents(req: IngestRequest):
    doc_dir = Path(req.directory)
    if not doc_dir.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {req.directory}")

    docs = []
    files_processed = 0

    for root, _, files in os.walk(doc_dir):
        for fname in files:
            fpath = Path(root) / fname
            suffix = fpath.suffix.lower()
            if suffix not in LOADERS:
                continue
            try:
                loader = LOADERS[suffix](str(fpath))
                loaded = loader.load()
                # Tag with category from parent folder name
                category = Path(root).name  # "av" or "ev"
                for doc in loaded:
                    doc.metadata["source"] = fname
                    doc.metadata["category"] = category
                docs.extend(loaded)
                files_processed += 1
            except Exception as e:
                print(f"Skipping {fpath}: {e}")

    if not docs:
        raise HTTPException(status_code=400, detail="No documents found to ingest.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    settings = RAGSettings()
    if settings.vectorstore_type.lower() == "faiss":
        from langchain_community.vectorstores import FAISS
        vs = FAISS.from_documents(chunks, embeddings)
        vs.save_local(settings.faiss_persist_dir)
    else:
        from langchain_community.vectorstores import Chroma
        Chroma.from_documents(
            chunks,
            embeddings,
            collection_name="langchain",
            persist_directory=settings.chroma_persist_dir,
        )

    return IngestResponse(
        status="success",
        chunks_created=len(chunks),
        files_processed=files_processed,
    )
