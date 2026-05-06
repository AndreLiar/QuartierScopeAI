"""QS-023 — Tavily web search wrapper with SSRF guard.

Returns clean snippet results suitable for RAG-style consumption.
Filters out private/loopback hosts in the response (SSRF defence).
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from tavily import AsyncTavilyClient

from app.config import settings
from app.security import is_private_or_loopback

logger = logging.getLogger(__name__)


async def search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY not set — web search disabled, returning []")
        return []

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    response: dict[str, Any] = await client.search(
        query=query,
        max_results=max_results,
        include_answer=False,
        search_depth="basic",
    )

    safe: list[dict[str, Any]] = []
    for r in response.get("results", []):
        url = r.get("url", "")
        host = urlparse(url).hostname or ""
        if not host or is_private_or_loopback(host):
            logger.warning("ssrf-guard: skipping result with host=%r url=%r", host, url)
            continue
        safe.append(
            {
                "title": r.get("title", ""),
                "url": url,
                "content": r.get("content", ""),
                "score": float(r.get("score", 0.0)),
            }
        )
    return safe
