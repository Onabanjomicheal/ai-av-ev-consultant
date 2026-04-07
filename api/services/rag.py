"""
RAG service — the core retrieval-augmented generation pipeline.

Flow:
  question → classify → embed → retrieve → rerank → build prompt → LLM
"""
from __future__ import annotations
import logging
from pathlib import Path
import re
from pydantic_settings import BaseSettings

from api.services.embedder import embed_query, Settings as EmbedSettings
from core.query_router import classify_query, QueryCategory
from core.prompt_builder import build_messages
from core.reranker import rerank

logger = logging.getLogger(__name__)


class RAGSettings(BaseSettings):
    chroma_persist_dir: str = "./data/vectorstore"
    retrieval_k: int = 8
    rerank_top_n: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


# ── Vector store loader ────────────────────────────────────────────

def _load_vectorstore(settings: RAGSettings):
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name=EmbedSettings().embedding_model)

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
    domain = _detect_domain(question)
    logger.info(f"Query category: {category} | domain: {domain or 'unknown'}")

    try:
        vs = _load_vectorstore(settings)
    except Exception as e:
        logger.warning(f"Vector store not ready: {e}")
        return []

    search_kwargs: dict = {"k": settings.retrieval_k}
    if domain:
        # Ingest tags docs with domain="av" or "ev" (folder name)
        search_kwargs["filter"] = {"domain": domain}

    try:
        docs = vs.similarity_search(question, **search_kwargs)
    except Exception:
        docs = []

    if not docs:
        # Fallback to unfiltered search if filter was too strict or missing metadata.
        docs = vs.similarity_search(question, k=settings.retrieval_k)

    chunks = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
        }
        for doc in docs
    ]

    chunks = _prioritize_sources_by_question(question, chunks)
    return rerank(question, chunks, top_n=settings.rerank_top_n)


def _detect_domain(question: str) -> str | None:
    q = question.lower()
    av_keywords = [
        "av", "autonomous", "ads", "adas", "sae j3016", "wp.29",
        "nhtsa", "incident", "sgo", "od d", "operational design domain",
        "automated driving", "self-driving",
    ]
    ev_keywords = [
        "ev", "electric vehicle", "bev", "phev", "battery",
        "charging", "ccs", "chademo", "nacs", "v2g", "v2h",
        "battery regulation", "zev",
    ]
    av_hit = any(k in q for k in av_keywords)
    ev_hit = any(k in q for k in ev_keywords)
    if av_hit and not ev_hit:
        return "av"
    if ev_hit and not av_hit:
        return "ev"
    return None


def _prioritize_sources_by_question(question: str, chunks: list[dict]) -> list[dict]:
    """
    If the question mentions a doc name or strong tokens (e.g., 'SAE', 'J3016'),
    prioritize chunks whose source filename contains those tokens.
    """
    q = question.lower()
    # Exact filename hint
    m = re.search(r"([A-Za-z0-9_.-]+\\.pdf)", question)
    if m:
        fname = m.group(1).lower()
        exact = [c for c in chunks if fname == str(c.get("source", "")).lower()]
        return exact or chunks

    # Token-based hint (prefer filenames containing key tokens)
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9_.-]+", question)]
    tokens = [t for t in tokens if len(t) >= 4]
    if not tokens:
        return chunks

    def score(c: dict) -> int:
        src = str(c.get("source", "")).lower()
        return sum(1 for t in tokens if t in src)

    scored = sorted(chunks, key=score, reverse=True)
    # If top has zero score, no meaningful match
    return scored if score(scored[0]) > 0 else chunks


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
