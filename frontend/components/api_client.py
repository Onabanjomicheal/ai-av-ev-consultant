"""
Shared HTTP client utilities for Streamlit pages.
Adds consistent timeouts, retries, and warm-up health check.
"""
from __future__ import annotations
import time
import httpx
import streamlit as st


DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


@st.cache_resource
def get_client() -> httpx.Client:
    return httpx.Client(timeout=DEFAULT_TIMEOUT)


def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(2 ** attempt, 8))


def request_with_retry(method: str, url: str, max_attempts: int = 3, **kwargs) -> httpx.Response:
    last_err = None
    client = get_client()
    for attempt in range(max_attempts):
        try:
            return client.request(method, url, **kwargs)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as e:
            last_err = e
            _sleep_backoff(attempt)
    raise last_err if last_err else RuntimeError("Request failed")


def stream_with_retry(method: str, url: str, max_attempts: int = 2, **kwargs):
    last_err = None
    client = get_client()
    for attempt in range(max_attempts):
        try:
            return client.stream(method, url, **kwargs)
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as e:
            last_err = e
            _sleep_backoff(attempt)
    raise last_err if last_err else RuntimeError("Stream failed")


@st.cache_data(ttl=300)
def warmup(api_url: str) -> bool:
    try:
        resp = request_with_retry("GET", f"{api_url}/health")
        return resp.status_code == 200
    except Exception:
        return False
