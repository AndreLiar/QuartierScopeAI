"""QS-070 — Langfuse v2 callback wiring.

Returns the LangChain callback list for any LLM invocation. If Langfuse keys
are not configured, returns [] silently — the app still runs, just without
traces. No fail-closed behaviour: observability is opt-in.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _handler() -> Any | None:
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    try:
        from langfuse.callback import CallbackHandler

        return CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host or "http://langfuse-server:3000",
        )
    except Exception as exc:
        logger.warning("langfuse-init-failed: %s", exc)
        return None


def callbacks() -> list[Any]:
    """Return [] when Langfuse isn't configured. Pass to LLM invocations as
    `config={"callbacks": observability.callbacks()}`."""
    handler = _handler()
    return [handler] if handler else []


def trace_config(name: str | None = None, metadata: dict | None = None) -> dict[str, Any]:
    """Convenience: build a LangChain `config` dict with callbacks + tags."""
    cfg: dict[str, Any] = {"callbacks": callbacks()}
    if name:
        cfg["run_name"] = name
    if metadata:
        cfg["metadata"] = metadata
    return cfg
