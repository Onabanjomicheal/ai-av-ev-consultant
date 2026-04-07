import time
import uuid
from fastapi import Request

try:
    from loguru import logger
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("av_ev_consultant")


async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(f"[{request_id}] → {response.status_code} ({elapsed:.1f}ms)")
    return response
