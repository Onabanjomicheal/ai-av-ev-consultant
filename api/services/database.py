"""
Supabase client singleton.
Used for: users, session logs, saved queries, feedback.
"""
from __future__ import annotations
from functools import lru_cache
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class DBSettings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_db():
    s = DBSettings()
    key = s.supabase_service_key or s.supabase_key
    if not s.supabase_url or not key:
        return None
    from supabase import create_client
    return create_client(s.supabase_url, key)


def log_query(session_id: str, question: str, answer: str, sources: list[str]) -> bool:
    db = get_db()
    if db is None:
        logger.warning("Supabase not configured; skipping query log.")
        return False
    try:
        db.table("query_logs").insert({
            "session_id": session_id,
            "question": question,
            "answer": answer[:2000],
            "sources": sources,
        }).execute()
        return True
    except Exception:
        logger.exception("Failed to insert query log into Supabase.")
        return False
