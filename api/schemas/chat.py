from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str


class ClearSessionRequest(BaseModel):
    session_id: str
