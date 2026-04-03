"""
RAG service — the core retrieval-augmented generation pipeline.

Flow:
  question → classify → embed → retrieve → rerank → build prompt → LLM
"""
from __future__ import annotations
import logging
from pathlib import Path
from pydantic_settings import BaseSettings

from api.services.embedder import embed_query
from core.query_router import classify_query, QueryCategory
from core.prompt_builder import build_messages
from core.reranker import rerank

logger = logging.getLogger(__name__)


class RAGSettings(BaseSettings):
    vectorstore_type: str = "chroma"
    chroma_persist_dir: str = "./data/vectorstore"
    faiss_persist_dir: str = "./data/vectorstore_faiss"
    retrieval_k: int = 8
    rerank_top_n: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


# ── Vector store loader ────────────────────────────────────────────

def _load_vectorstore(settings: RAGSettings):
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if settings.vectorstore_type.lower() == "faiss":
        from langchain_community.vectorstores import FAISS
        # FAISS index must already be built and saved locally
        return FAISS.load_local(
            settings.faiss_persist_dir,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    from langchain_community.vectorstores import Chroma
    return Chroma(
        collection_name="langchain",
        persist_directory=settings.chroma_persist_dir,
        embedding_function=embeddings,
    )


# ── Retrieval ──────────────────────────────────────────────────────

def retrieve(question: str, settings: RAGSettings | None = None) -> list[dict]:
    """
    Retrieve and rerank relevant chunks for a question.
    Returns list of {"content": str, "source": str}.
    """
    if settings is None:
        settings = RAGSettings()

    category = classify_query(question)
    logger.info(f"Query category: {category}")

    try:
        vs = _load_vectorstore(settings)
    except Exception as e:
        logger.warning(f"Vector store not ready: {e}")
        return []

    search_kwargs: dict = {"k": settings.retrieval_k}
    if category != QueryCategory.GENERAL:
        search_kwargs["filter"] = {"category": category.value}

    try:
        docs = vs.similarity_search(question, **search_kwargs)
    except Exception:
        docs = []

    if not docs:
        docs = vs.similarity_search(question, k=settings.retrieval_k)

    chunks = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
        }
        for doc in docs
    ]

    return rerank(question, chunks, top_n=settings.rerank_top_n)


# ── Full RAG chain ─────────────────────────────────────────────────

async def rag_stream(
    question: str,
    history: list[dict],
    settings: RAGSettings | None = None,
    data_summary: str = "",
):
    """
    Async generator yielding LLM response tokens.
    Caller is responsible for saving history.
    """
    from api.services.llm import stream_response

    if data_summary:
        messages = build_messages(question, [], history, data_summary=data_summary)
        yield "__SOURCES__:\n"
    else:
        chunks = retrieve(question, settings)
        messages = build_messages(question, chunks, history)
        sources = list({c["source"] for c in chunks})
        yield f"__SOURCES__:{','.join(sources)}\n"

    async for token in stream_response(messages):
        yield token
