"""QS-021/022/023 wired together as the Tools agent.

Aggregates read-only data tools: DVF discovery, web search, (HubSpot read).
Returns both raw data and a citations-ready sources list.
"""

from __future__ import annotations

import logging
import re
from typing import TypedDict

from app.tools import dvf, web_search

logger = logging.getLogger(__name__)

# Major French cities → INSEE codes. Easy heuristic for the Sarah scenario.
# v1.5: replace with the BAN/INSEE search API for any commune.
COMMUNE_HINTS: dict[str, str] = {
    "lyon 7e": "69387",
    "lyon 7": "69387",
    "lyon 1er": "69381",
    "lyon 2e": "69382",
    "lyon 3e": "69383",
    "paris 11e": "75111",
    "paris 18e": "75118",
    "marseille": "13055",
    "bordeaux": "33063",
    "lille": "59350",
    "toulouse": "31555",
    "nantes": "44109",
    "rennes": "35238",
    "strasbourg": "67482",
    "lyon": "69123",
    "paris": "75056",
}


class ToolsResult(TypedDict):
    data: dict
    sources: list[dict]


def _extract_commune(query: str) -> tuple[str | None, str | None]:
    q = query.lower()
    for hint, insee in sorted(COMMUNE_HINTS.items(), key=lambda x: -len(x[0])):
        if hint in q:
            return hint, insee
    m = re.search(r"\b(\d{5})\b", q)
    if m:
        return None, m.group(1)
    return None, None


async def run_tools(query: str) -> ToolsResult:
    label, insee = _extract_commune(query)

    data: dict = {}
    sources: list[dict] = []

    if insee:
        try:
            stats = await dvf.query_transactions(insee, year_from=2024)
            data["dvf"] = {"commune": label or insee, **stats}
            sources.extend(stats.get("sources", []))
        except Exception as exc:
            logger.warning("tools-dvf-failed: %s", exc)

    try:
        web = await web_search.search(query, max_results=3)
        if web:
            data["web"] = web
            sources.extend(
                {"name": r["title"], "url": r["url"], "description": r["content"][:200]}
                for r in web
            )
    except Exception as exc:
        logger.warning("tools-web-failed: %s", exc)

    return {"data": data, "sources": sources}
