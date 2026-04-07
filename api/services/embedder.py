"""
Singleton sentence-transformer embedder.
Model loads once on first call; reused for all subsequent requests.
"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    # Import lazily to reduce startup memory footprint
    from sentence_transformers import SentenceTransformer
    settings = Settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True)
    if hasattr(vectors, "tolist"):
        return vectors.tolist()
    return [list(v) for v in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
