"""
Cross-encoder reranker.
After FAISS/Chroma retrieves top-k chunks by embedding similarity,
the reranker scores each (question, chunk) pair more precisely and
re-orders — cutting noise before the LLM sees the context.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (free, ~80 MB).
Falls back gracefully if FlagEmbedding is unavailable.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

_reranker = None


def _load_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    try:
        from FlagEmbedding import FlagReranker
        _reranker = FlagReranker(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            use_fp16=True,
        )
        logger.info("Reranker loaded: cross-encoder/ms-marco-MiniLM-L-6-v2")
    except Exception as e:
        logger.warning(f"Reranker unavailable, skipping: {e}")
        _reranker = None
    return _reranker


def rerank(question: str, chunks: list[dict], top_n: int = 4) -> list[dict]:
    """
    Re-orders chunks by cross-encoder relevance score.

    Args:
        question: User question string.
        chunks: List of {"content": str, "source": str} dicts.
        top_n: How many to return after reranking.

    Returns:
        Sorted list, most relevant first, truncated to top_n.
    """
    if not chunks:
        return chunks

    reranker = _load_reranker()
    if reranker is None:
        return chunks[:top_n]

    pairs = [[question, c["content"]] for c in chunks]
    scores = reranker.compute_score(pairs)

    scored = sorted(
        zip(scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )
    return [chunk for _, chunk in scored[:top_n]]
