"""QS-021 — DVF tool: discover Cerema API via data.gouv MCP, then call it.

The data.gouv MCP exposes `search_dataservices` and `get_dataservice_openapi_spec`.
We use them to discover the *API Données Foncières* (Cerema), parse its OpenAPI
spec, and call the right endpoint for transactions on a given commune.

Discovery is cached in Redis with a 24h TTL — Cerema's API metadata is stable.

Fallback (QS-022): if Cerema returns 5xx or rate-limits, query DVF locally with
DuckDB over the cached `.csv.gz` from data.gouv.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

import httpx
import redis.asyncio as redis_async

from app.config import settings
from app.tools.datagouv_mcp import DataGouvMCP

logger = logging.getLogger(__name__)

DISCOVERY_CACHE_KEY = "qs:dvf:discovery"
DISCOVERY_TTL = 24 * 3600


class DvfDiscovery(TypedDict):
    name: str
    base_url: str
    description: str
    openapi_url: str | None


DEFAULT_DISCOVERY: DvfDiscovery = {
    "name": "API Données Foncières (Cerema)",
    "base_url": "",
    "description": "Données ouvertes de transactions immobilières DVF, publiées par le Cerema",
    "openapi_url": None,
}


class TransactionStats(TypedDict):
    code_insee: str
    year_from: int
    year_to: int | None
    count: int
    median_eur_per_m2: float | None
    sources: list[dict[str, str]]


async def _redis() -> redis_async.Redis | None:
    try:
        client = redis_async.from_url(settings.redis_url, decode_responses=True, socket_timeout=2)
        await client.ping()
        return client
    except Exception as exc:
        logger.warning("redis-unavailable: %s — proceeding without cache", exc)
        return None


async def discover_cerema_api(force_refresh: bool = False) -> DvfDiscovery:
    """Find the Cerema DVF dataservice via data.gouv MCP. Falls back to a sensible default."""
    cache = await _redis()
    if cache is not None and not force_refresh:
        try:
            cached = await cache.get(DISCOVERY_CACHE_KEY)
            if cached:
                logger.info("dvf-discovery: cache hit")
                return json.loads(cached)
        except Exception as exc:
            logger.warning("redis-get-failed: %s", exc)

    discovery: DvfDiscovery = dict(DEFAULT_DISCOVERY)  # type: ignore[assignment]
    try:
        logger.info("dvf-discovery: querying data.gouv MCP search_dataservices")
        async with DataGouvMCP() as mcp:
            results = await mcp.call("search_dataservices", q="DVF demandes valeurs foncières")
        candidates = _extract_dataservices(results)
        cerema = next(
            (
                c
                for c in candidates
                if "foncière" in c.get("name", "").lower() or "DVF" in c.get("name", "")
            ),
            candidates[0] if candidates else None,
        )
        if cerema is not None:
            discovery = {
                "name": cerema.get("name") or DEFAULT_DISCOVERY["name"],
                "base_url": cerema.get("base_url") or "",
                "description": cerema.get("description") or DEFAULT_DISCOVERY["description"],
                "openapi_url": cerema.get("openapi_url"),
            }
        else:
            logger.warning("dvf-discovery: no candidate from MCP, using default")
    except Exception as exc:
        logger.warning("dvf-discovery: MCP call failed (%s) — using default", exc)

    if cache is not None:
        try:
            await cache.setex(DISCOVERY_CACHE_KEY, DISCOVERY_TTL, json.dumps(discovery))
        except Exception as exc:
            logger.warning("redis-set-failed: %s", exc)
    return discovery


def _extract_dataservices(mcp_result: Any) -> list[dict[str, Any]]:
    """Normalise MCP `search_dataservices` content into a list of dataservice dicts."""
    if mcp_result is None:
        return []
    if isinstance(mcp_result, list):
        items: list[dict[str, Any]] = []
        for item in mcp_result:
            text = getattr(item, "text", None)
            payload = item if isinstance(item, dict) else {}
            if text:
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
            if isinstance(payload, dict):
                if "data" in payload and isinstance(payload["data"], list):
                    items.extend(payload["data"])
                elif "results" in payload and isinstance(payload["results"], list):
                    items.extend(payload["results"])
                else:
                    items.append(payload)
        return items
    if isinstance(mcp_result, dict):
        if "data" in mcp_result and isinstance(mcp_result["data"], list):
            return mcp_result["data"]
        if "results" in mcp_result and isinstance(mcp_result["results"], list):
            return mcp_result["results"]
        return [mcp_result]
    return []


async def query_transactions(
    code_insee: str,
    year_from: int = 2024,
    year_to: int | None = None,
) -> TransactionStats:
    """Query DVF transactions for a commune.

    For Sprint 2, returns a stub structure populated from MCP discovery only.
    The actual Cerema call is wired in QS-022 once the discovery contract is verified.
    """
    discovery = await discover_cerema_api()
    sources: list[dict[str, str]] = [
        {
            "name": discovery["name"],
            "url": discovery.get("base_url") or "",
            "description": (discovery.get("description") or "")[:200],
        }
    ]

    return {
        "code_insee": code_insee,
        "year_from": year_from,
        "year_to": year_to,
        "count": 0,
        "median_eur_per_m2": None,
        "sources": sources,
    }


async def cerema_get(path: str, params: dict[str, str | int] | None = None) -> dict[str, Any]:
    """Authenticated-or-not GET to the Cerema API. Wired in QS-022."""
    discovery = await discover_cerema_api()
    if not discovery["base_url"]:
        raise RuntimeError("Cerema API base_url not discoverable via data.gouv MCP")

    url = discovery["base_url"].rstrip("/") + "/" + path.lstrip("/")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params=params or {})
        r.raise_for_status()
        return r.json()
