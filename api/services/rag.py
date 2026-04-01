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
    retrieval_k: int = 8        # chunks fetched from vector store
    rerank_top_n: int = 4       # chunks kept after reranking

    class Config:
        env_file = ".env"
        extra = "ignore"


# ── Vector store loader ────────────────────────────────────────────

def _load_vectorstore(settings: RAGSettings):
    if settings.vectorstore_type == "chroma":
        from langchain_community.vectorstores import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return Chroma(
            persist_directory=settings.chroma_persist_dir,
            embedding_function=embeddings,
        )
    else:
        import faiss
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        index_path = Path(settings.chroma_persist_dir) / "faiss_index"
        return FAISS.load_local(str(index_path), embeddings)


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

    # Category-based filter (optional metadata filter for Chroma)
    search_kwargs: dict = {"k": settings.retrieval_k}
    if category != QueryCategory.GENERAL:
        search_kwargs["filter"] = {"category": category.value}

    try:
        docs = vs.similarity_search(question, **search_kwargs)
    except Exception:
        # Retry without category filter if no results
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
):
    """
    Async generator yielding LLM response tokens.
    Caller is responsible for saving history.
    """
    from api.services.llm import stream_response

    chunks = retrieve(question, settings)
    messages = build_messages(question, chunks, history)

    sources = list({c["source"] for c in chunks})
    yield f"__SOURCES__:{','.join(sources)}\n"  # metadata line

    async for token in stream_response(messages):
        yield token
