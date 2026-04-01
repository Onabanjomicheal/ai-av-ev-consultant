"""
FastAPI application entry point.
Run: uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import chat, ingest, search, auth
from api.middleware.logging import log_requests

app = FastAPI(
    title="AV/EV Consultant Assistant API",
    description="RAG-powered assistant for autonomous and electric vehicle practitioners and policy makers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(auth.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "av_ev_consultant_api"}
