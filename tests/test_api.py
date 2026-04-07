import asyncio
from httpx import AsyncClient, ASGITransport
from api.main import app


def _run(coro):
    return asyncio.run(coro)


def test_health():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    _run(_test())


def test_chat_missing_fields():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/chat/stream", json={})
        assert resp.status_code == 422
    _run(_test())


def test_clear_session():
    async def _test():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/chat/clear", json={"session_id": "test-123"})
        assert resp.status_code == 200
    _run(_test())
