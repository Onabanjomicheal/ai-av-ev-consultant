import pytest
from unittest.mock import patch, MagicMock
from core.query_router import classify_query, QueryCategory
from core.prompt_builder import build_messages
from core.reranker import rerank


def test_classify_technical():
    assert classify_query("How does LiDAR sensor fusion work?") == QueryCategory.TECHNICAL


def test_classify_regulatory():
    assert classify_query("What does SAE J3016 regulation say about Level 3?") == QueryCategory.REGULATORY


def test_classify_market():
    assert classify_query("What is the EV adoption market share forecast?") == QueryCategory.MARKET


def test_classify_general():
    assert classify_query("Tell me about cars") == QueryCategory.GENERAL


def test_prompt_builder_returns_messages():
    msgs = build_messages(
        "What is a BMS?",
        [{"content": "BMS stands for Battery Management System.", "source": "ev_guide.pdf"}],
        [],
    )
    assert len(msgs) >= 2  # system + human


def test_rerank_fallback_no_reranker():
    chunks = [
        {"content": "LiDAR is a sensor.", "source": "a.pdf"},
        {"content": "Battery management system.", "source": "b.pdf"},
    ]
    result = rerank("What is LiDAR?", chunks, top_n=2)
    assert len(result) <= 2
