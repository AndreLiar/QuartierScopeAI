"""Actions agent — write tools (HubSpot, Slack, email).

Plan-only by default; never executes without explicit confirmation. Wire in QS-051/052.
"""

from app.config import settings


async def propose(result: dict, deal_id: str | None) -> list[dict]:
    if not settings.hubspot_enabled or not deal_id:
        return []
    return [
        {"tool": "hubspot_create_note", "deal_id": deal_id, "preview": "stub"},
        {"tool": "hubspot_update_property", "deal_id": deal_id, "props": {}},
    ]


async def execute(plan: list[dict]) -> list[dict]:
    """Run only after user confirmation. Wire in QS-051."""
    return [{"tool": p["tool"], "status": "stub"} for p in plan]
