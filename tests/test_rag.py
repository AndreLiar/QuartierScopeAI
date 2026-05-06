"""QS-032 acceptance tests — RAG retrieval + citation enforcement.

Live Qdrant + corpus tests run only when QS_INTEGRATION=1.
Without the env flag, only resilience tests run (no key / no Qdrant).
"""

from __future__ import annotations

import os

import pytest

from app.agents import rag_agent


@pytest.mark.asyncio
async def test_refuses_when_no_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "openai_api_key", "")
    result = await rag_agent.retrieve("Comment scorer un quartier locatif ?")
    assert result["refused"] is True
    assert result["chunks"] == []
    assert result["citations"] == []


@pytest.mark.asyncio
async def test_refuses_when_qdrant_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "openai_api_key", "sk-fake-for-test")
    monkeypatch.setattr(config.settings, "qdrant_url", "http://qdrant-not-here:9999")
    result = await rag_agent.retrieve("anything")
    assert result["refused"] is True


@pytest.mark.skipif(os.getenv("QS_INTEGRATION") != "1", reason="needs live Qdrant + corpus")
@pytest.mark.asyncio
async def test_live_retrieval_returns_citations() -> None:
    result = await rag_agent.retrieve("méthode de scoring quartier locatif", k=5)
    assert result["refused"] is False
    assert len(result["citations"]) > 0
    for c in result["citations"]:
        assert c["source"]
        assert c["score"] >= 0.0
