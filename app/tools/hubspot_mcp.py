"""QS-050 + QS-051 — HubSpot REST client (Service Key bearer).

Free-tier compatible. Uses the standard CRM v3 endpoints. The "MCP" in the
filename is aspirational — once HubSpot's MCP Auth Apps leaves beta, we
swap the implementation behind these same async functions.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
BASE_URL = "https://api.hubapi.com"


def _headers() -> dict[str, str]:
    if not settings.hubspot_token:
        raise RuntimeError("HUBSPOT_TOKEN not set — Actions agent disabled")
    return {
        "Authorization": f"Bearer {settings.hubspot_token}",
        "Content-Type": "application/json",
    }


async def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request(method, f"{BASE_URL}{path}", headers=_headers(), **kwargs)
        r.raise_for_status()
        return r.json() if r.content else {}


async def get_contact(contact_id: str) -> dict[str, Any]:
    return await _request("GET", f"/crm/v3/objects/contacts/{contact_id}")


async def get_deal(deal_id: str) -> dict[str, Any]:
    return await _request(
        "GET",
        f"/crm/v3/objects/deals/{deal_id}",
        params={"properties": "dealname,amount,dealstage,pipeline,closedate"},
    )


async def create_note(deal_id: str, body: str) -> dict[str, Any]:
    """Create a note engagement and associate it with the deal."""
    note = await _request(
        "POST",
        "/crm/v3/objects/notes",
        json={
            "properties": {
                "hs_note_body": body,
                "hs_timestamp": _now_ms(),
            }
        },
    )
    note_id = note["id"]
    await _request(
        "PUT",
        f"/crm/v3/objects/notes/{note_id}/associations/deals/{deal_id}/note_to_deal",
    )
    return note


async def update_property(deal_id: str, props: dict[str, Any]) -> dict[str, Any]:
    return await _request(
        "PATCH",
        f"/crm/v3/objects/deals/{deal_id}",
        json={"properties": props},
    )


async def create_task(deal_id: str, title: str, body: str = "") -> dict[str, Any]:
    task = await _request(
        "POST",
        "/crm/v3/objects/tasks",
        json={
            "properties": {
                "hs_task_subject": title,
                "hs_task_body": body,
                "hs_task_status": "NOT_STARTED",
                "hs_task_priority": "MEDIUM",
                "hs_timestamp": _now_ms(),
            }
        },
    )
    task_id = task["id"]
    await _request(
        "PUT",
        f"/crm/v3/objects/tasks/{task_id}/associations/deals/{deal_id}/task_to_deal",
    )
    return task


def _now_ms() -> int:
    import time

    return int(time.time() * 1000)
