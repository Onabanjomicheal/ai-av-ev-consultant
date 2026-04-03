"""
Assembles the final prompt sent to the LLM from:
  - system prompt
  - retrieved document chunks (context)
  - conversation history
  - current user question
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.system_prompt import SYSTEM_PROMPT
from core.spec_compare import build_spec_table


def build_messages(
    question: str,
    context_chunks: list[dict],
    history: list[dict],
    data_summary: str = "",
) -> list:
    """
    Returns a list of LangChain message objects ready for chat LLMs.

    Args:
        question: Current user question.
        context_chunks: List of {"content": str, "source": str} dicts from RAG.
        history: List of {"role": "user"|"assistant", "content": str}.
        data_summary: Optional data findings from pandas query.
    """
    if data_summary:
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"---\nDATA FINDINGS (use ONLY this to answer, do not guess):\n"
            f"{data_summary}\n---\n"
            f"Interpret this data as a consultant. Give insights and recommendations "
            f"based strictly on the numbers provided."
        )
        messages = [SystemMessage(content=system_content)]
        for turn in history:
            if turn["role"] == "user":
                messages.append(HumanMessage(content=turn["content"]))
            else:
                messages.append(AIMessage(content=turn["content"]))
        messages.append(HumanMessage(content=question))
        return messages

    context_block = _format_context(context_chunks)

    mode_note = _mode_instructions(question)
    spec_table = ""
    if _is_spec_mode(question):
        spec_table = build_spec_table(question, context_chunks)

    system_content = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{mode_note}\n"
        f"---\nRELEVANT DOCUMENT CONTEXT:\n{context_block}\n---"
    )
    if spec_table:
        system_content += f"\n\nEXTRACTED SPEC TABLE:\n{spec_table}"

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


def _mode_instructions(question: str) -> str:
    q = question.lower()
    notes = []

    if any(k in q for k in ["briefing", "brief", "executive summary", "exec summary"]):
        notes.append(
            "BRIEFING MODE: Use sections Context, Key Points, Risks, Recommendations, Sources."
        )

    if any(k in q for k in ["compare", "comparison", "vs", "versus", "side by side", "spec"]):
        notes.append(
            "SPEC COMPARISON MODE: Provide a side-by-side table. Use only facts from sources; "
            "write 'Not stated in sources' for missing fields."
        )

    if not notes:
        return ""
    return "MODE NOTES:\n" + "\n".join(notes)


def _is_spec_mode(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in ["compare", "comparison", "vs", "versus", "side by side", "spec"])
