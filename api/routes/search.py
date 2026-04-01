from fastapi import APIRouter, Query
from api.services.rag import retrieve

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_documents(
    q: str = Query(..., min_length=1),
    k: int = Query(default=5, ge=1, le=20),
):
    """
    Direct semantic search over the document store.
    Returns ranked chunks with sources — useful for the policy search page.
    """
    from api.services.rag import RAGSettings
    settings = RAGSettings(retrieval_k=k, rerank_top_n=k)
    chunks = retrieve(q, settings)
    return {"query": q, "results": chunks}
