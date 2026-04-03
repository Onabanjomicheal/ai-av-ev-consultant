"""
FastAPI application entry point.
Run: uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic_settings import BaseSettings

from api.routes import chat, ingest, search, auth
from api.middleware.logging import log_requests

class AppSettings(BaseSettings):
    env: str = "dev"
    cors_origins: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


def _parse_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(
    title="AV/EV Consultant Assistant API",
    description="RAG-powered assistant for autonomous and electric vehicle practitioners and policy makers.",
    version="1.0.0",
)

settings = AppSettings()
origins = _parse_origins(settings.cors_origins)
if settings.env.lower() != "prod":
    # Wide-open CORS in dev for local Streamlit + API iteration
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
