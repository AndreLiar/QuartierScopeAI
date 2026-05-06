"""Redis-backed LangGraph checkpointer. Wire in QS-043."""

from app.config import settings


def get_checkpointer():  # type: ignore[no-untyped-def]
    """Returns a LangGraph checkpointer connected to Redis. Stub for QS-043."""
    return None
