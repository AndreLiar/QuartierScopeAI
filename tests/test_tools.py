"""QS-021 / QS-023 acceptance tests for Tools agent components."""

from __future__ import annotations

import pytest

from app.tools import dvf, web_search


@pytest.mark.asyncio
async def test_dvf_discovery_returns_dataservice() -> None:
    discovery = await dvf.discover_cerema_api(force_refresh=True)
    assert discovery["name"]
    assert "base_url" in discovery
    assert "description" in discovery


@pytest.mark.asyncio
async def test_dvf_query_transactions_returns_typed_dict() -> None:
    stats = await dvf.query_transactions("69387", year_from=2024)
    assert stats["code_insee"] == "69387"
    assert stats["year_from"] == 2024
    assert isinstance(stats["sources"], list)


@pytest.mark.asyncio
async def test_web_search_disabled_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "tavily_api_key", "")
    results = await web_search.search("anything")
    assert results == []


def test_extract_dataservices_handles_dict() -> None:
    payload = {"data": [{"name": "Service A"}, {"name": "Service B"}]}
    items = dvf._extract_dataservices(payload)
    assert len(items) == 2
    assert items[0]["name"] == "Service A"


def test_extract_dataservices_handles_text_content() -> None:
    class FakeContent:
        text = '{"data": [{"name": "DVF API"}]}'

    items = dvf._extract_dataservices([FakeContent()])
    assert len(items) == 1
    assert items[0]["name"] == "DVF API"
