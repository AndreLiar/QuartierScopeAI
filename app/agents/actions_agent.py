"""QS-051 + QS-052 — Actions agent: proposes HubSpot writes, never executes
without explicit confirmation.

Two-phase contract:
1. propose(synth_result, deal_id) → returns a list of planned action dicts
   (no side-effects). Each item has tool, args, preview.
2. execute(plan) → only called when the user has confirmed (`y` in CLI or
   `confirm: true` in API). Calls real HubSpot endpoints.

If HUBSPOT_TOKEN is empty → propose() returns [] (the agent is silently
disabled), and execute() refuses to run.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TypedDict

from app.config import settings
from app.tools import hubspot_mcp

logger = logging.getLogger(__name__)


class PlannedAction(TypedDict):
    tool: str
    args: dict
    preview: str


def _format_brief_for_note(query: str, synth_answer: str, citations: list[dict]) -> str:
    parts = [f"<b>QuartierScope AI — analyse de quartier</b>", f"<i>Question:</i> {query}", ""]
    parts.append(synth_answer)
    if citations:
        parts.append("")
        parts.append("<b>Sources :</b>")
        for c in citations:
            url = c.get("url") or ""
            name = c.get("source", "?")
            if url:
                parts.append(f'  • <a href="{url}">{name}</a>')
            else:
                parts.append(f"  • {name}")
    return "<br/>".join(parts)


async def propose(
    query: str,
    synth_result: dict,
    deal_id: str | None,
) -> list[PlannedAction]:
    if not settings.hubspot_enabled:
        logger.info("actions-disabled: HUBSPOT_TOKEN absent")
        return []
    if not deal_id:
        return []
    if synth_result.get("refused"):
        return []

    answer = synth_result.get("answer", "")
    citations = synth_result.get("citations", [])
    body = _format_brief_for_note(query, answer, citations)

    plan: list[PlannedAction] = [
        {
            "tool": "hubspot_create_note",
            "args": {"deal_id": deal_id, "body": body},
            "preview": f"Note → deal {deal_id} ({len(citations)} sources)",
        },
        {
            "tool": "hubspot_update_property",
            "args": {
                "deal_id": deal_id,
                "props": {
                    "qs_last_analysis_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            "preview": f"Update deal {deal_id} → qs_last_analysis_at",
        },
    ]
    return plan


async def execute(plan: list[PlannedAction]) -> list[dict]:
    if not settings.hubspot_enabled:
        raise RuntimeError("Actions agent disabled (no HUBSPOT_TOKEN)")

    receipts: list[dict] = []
    for action in plan:
        tool = action["tool"]
        args = action["args"]
        try:
            if tool == "hubspot_create_note":
                result = await hubspot_mcp.create_note(args["deal_id"], args["body"])
            elif tool == "hubspot_update_property":
                result = await hubspot_mcp.update_property(args["deal_id"], args["props"])
            elif tool == "hubspot_create_task":
                result = await hubspot_mcp.create_task(
                    args["deal_id"], args["title"], args.get("body", "")
                )
            else:
                logger.warning("actions-unknown-tool: %s", tool)
                receipts.append({"tool": tool, "status": "error", "error": "unknown tool"})
                continue
            receipts.append({"tool": tool, "status": "ok", "id": result.get("id")})
        except Exception as exc:
            logger.warning("actions-execute-failed (%s): %s", tool, exc)
            receipts.append({"tool": tool, "status": "error", "error": str(exc)[:200]})
    return receipts
