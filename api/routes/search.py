from fastapi import APIRouter, Query
from api.services.rag import retrieve

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_documents(
    q: str = Query(..., min_length=1),
    k: int = Query(default=5, ge=1, le=20),
):
    from api.services.rag import RAGSettings
    settings = RAGSettings(retrieval_k=k*2, rerank_top_n=k)
    chunks = retrieve(q, settings)

    # Deduplicate by content
    seen = set()
    unique = []
    for chunk in chunks:
        key = chunk["content"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(chunk)

    return {"query": q, "results": unique[:k]}