"""
Conversation memory backed by Upstash Redis.
Each session gets its own key: "session:{session_id}".
Falls back to in-memory list when Redis is unavailable.
"""
from __future__ import annotations
import json
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

MAX_HISTORY = 20  # turns kept per session


class RedisSettings(BaseSettings):
    redis_url: str = ""
    redis_token: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


def _get_client():
    s = RedisSettings()
    if not s.redis_url:
        return None
    try:
        from upstash_redis import Redis
        return Redis(url=s.redis_url, token=s.redis_token)
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None


_in_memory: dict[str, list] = {}


def get_history(session_id: str) -> list[dict]:
    client = _get_client()
    if client:
        raw = client.get(f"session:{session_id}")
        return json.loads(raw) if raw else []
    return _in_memory.get(session_id, [])


def append_turn(session_id: str, role: str, content: str) -> None:
    history = get_history(session_id)
    history.append({"role": role, "content": content})
    history = history[-MAX_HISTORY:]

    client = _get_client()
    if client:
        client.set(f"session:{session_id}", json.dumps(history), ex=86400)
    else:
        _in_memory[session_id] = history


def clear_session(session_id: str) -> None:
    client = _get_client()
    if client:
        client.delete(f"session:{session_id}")
    _in_memory.pop(session_id, None)
