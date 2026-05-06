"""HubSpot MCP client — Free-tier compatible. Wire in QS-050/051."""


async def get_contact(contact_id: str) -> dict:
    return {}


async def get_deal(deal_id: str) -> dict:
    return {}


async def create_note(deal_id: str, body: str) -> dict:
    return {"status": "stub"}


async def update_property(deal_id: str, props: dict) -> dict:
    return {"status": "stub"}


async def create_task(deal_id: str, title: str, body: str = "") -> dict:
    return {"status": "stub"}
