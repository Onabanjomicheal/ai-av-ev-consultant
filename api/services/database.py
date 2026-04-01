"""
Supabase client singleton.
Used for: users, session logs, saved queries, feedback.
"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings


class DBSettings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_db():
    s = DBSettings()
    if not s.supabase_url:
        return None
    from supabase import create_client
    return create_client(s.supabase_url, s.supabase_key)


def log_query(session_id: str, question: str, answer: str, sources: list[str]):
    db = get_db()
    if db is None:
        return
    try:
        db.table("query_logs").insert({
            "session_id": session_id,
            "question": question,
            "answer": answer[:2000],
            "sources": sources,
        }).execute()
    except Exception:
        pass  # non-critical
