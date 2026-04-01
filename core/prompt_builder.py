"""
Assembles the final prompt sent to the LLM from:
  - system prompt
  - retrieved document chunks (context)
  - conversation history
  - current user question
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.system_prompt import SYSTEM_PROMPT


def build_messages(
    question: str,
    context_chunks: list[dict],
    history: list[dict],
) -> list:
    """
    Returns a list of LangChain message objects ready for chat LLMs.

    Args:
        question: Current user question.
        context_chunks: List of {"content": str, "source": str} dicts from RAG.
        history: List of {"role": "user"|"assistant", "content": str}.
    """
    context_block = _format_context(context_chunks)

    system_content = (
        f"{SYSTEM_PROMPT}\n\n"
        f"---\nRELEVANT DOCUMENT CONTEXT:\n{context_block}\n---"
    )

    messages = [SystemMessage(content=system_content)]

    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=question))
    return messages


def _format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant documents retrieved."
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "unknown")
        content = chunk.get("content", "")
        parts.append(f"[{i}] SOURCE: {source}\n{content}")
    return "\n\n".join(parts)
