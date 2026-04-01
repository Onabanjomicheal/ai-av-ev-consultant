"""
LLM abstraction layer.
Supports: Ollama (local, free) and Claude API.
Switch via LLM_PROVIDER env var: "ollama" | "claude"
"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    llm_provider: str = "ollama"
    llm_model: str = "mistral"
    ollama_base_url: str = "http://localhost:11434"
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_llm():
    s = LLMSettings()
    if s.llm_provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=s.anthropic_api_key,
            temperature=0.2,
            max_tokens=2048,
        )
    else:
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=s.llm_model,
            base_url=s.ollama_base_url,
            temperature=0.2,
        )


async def stream_response(messages: list):
    """Async generator that yields text chunks from the LLM."""
    llm = get_llm()
    async for chunk in llm.astream(messages):
        if hasattr(chunk, "content") and chunk.content:
            yield chunk.content
