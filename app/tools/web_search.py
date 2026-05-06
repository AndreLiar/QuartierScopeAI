"""Tavily web search wrapper with SSRF guard. Wire in QS-023."""

from app.config import settings
from app.security import assert_url_is_public


async def search(query: str, max_results: int = 5) -> list[dict]:
    if not settings.tavily_api_key:
        return []
    return []


def safe_fetch_url(url: str) -> str | None:
    """Fetch a URL only if it points to a public host (SSRF defence)."""
    assert_url_is_public(url)
    return None
