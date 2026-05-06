"""QS-040 acceptance — LangGraph orchestrator end-to-end."""

from __future__ import annotations

import os

import pytest

from app import orchestrator


@pytest.mark.asyncio
async def test_run_returns_typed_result_when_apis_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "openai_api_key", "")
    monkeypatch.setattr(config.settings, "tavily_api_key", "")
    monkeypatch.setattr(config.settings, "hubspot_token", "")

    result = await orchestrator.run("Bon quartier pour T2 LMNP à Lyon 7e ?")

    assert "answer" in result
    assert isinstance(result["trace"], list)
    assert len(result["trace"]) >= 3, "expected router + at least 2 agent steps in trace"
    assert isinstance(result["citations"], list)
    assert isinstance(result["proposed_actions"], list)


@pytest.mark.asyncio
async def test_no_actions_when_no_deal_id(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "openai_api_key", "")
    monkeypatch.setattr(config.settings, "hubspot_token", "set-but-no-deal")

    result = await orchestrator.run("anything", deal_id=None)
    assert result["proposed_actions"] == []


@pytest.mark.skipif(os.getenv("QS_INTEGRATION") != "1", reason="needs OpenAI + corpus + MCP")
@pytest.mark.asyncio
async def test_live_full_flow_returns_answer_with_citations() -> None:
    result = await orchestrator.run("Quel est le devoir de conseil d'un CGP CIF ?")
    assert result["refused"] is False
    assert len(result["answer"]) > 50
    assert len(result["citations"]) > 0
