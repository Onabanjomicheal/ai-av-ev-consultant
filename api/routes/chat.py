from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas.chat import ChatRequest, ClearSessionRequest
from api.services import memory, rag
from api.services.database import log_query

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming chat endpoint.
    Returns server-sent-event style text stream.
    First line: __SOURCES__:doc1.pdf,doc2.pdf
    Subsequent lines: LLM tokens.
    """
    history = memory.get_history(req.session_id)

    async def generate():
        full_answer = []
        sources = []
        try:
            async for token in rag.rag_stream(
                req.question,
                history,
                data_summary=req.data_summary,
            ):
                if token.startswith("__SOURCES__:"):
                    sources = token.replace("__SOURCES__:", "").strip().split(",")
                    yield token
                else:
                    full_answer.append(token)
                    yield token
        except Exception as e:
            yield f"Error: {e}"

        answer_text = "".join(full_answer)
        memory.append_turn(req.session_id, "user", req.question)
        memory.append_turn(req.session_id, "assistant", answer_text)
        log_query(req.session_id, req.question, answer_text, sources)

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/clear")
async def clear_session(req: ClearSessionRequest):
    memory.clear_session(req.session_id)
    return {"status": "cleared", "session_id": req.session_id}


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    return {"history": memory.get_history(session_id)}
