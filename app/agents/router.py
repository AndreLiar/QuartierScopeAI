"""QS-041 — Router agent: classify the query into rag / tools / rag+tools.

Single LLM call to gpt-4o-mini with structured output. Falls back to
"rag+tools" (the safest superset) if the LLM call fails.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal, TypedDict

from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "router.txt"
ROUTER_MODEL = "gpt-4o-mini"


class RouterDecision(TypedDict):
    mode: Literal["rag", "tools", "rag+tools"]
    needs_action: bool
    rationale: str


def _system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


async def classify(query: str, deal_id: str | None = None) -> RouterDecision:
    fallback: RouterDecision = {
        "mode": "rag+tools",
        "needs_action": deal_id is not None,
        "rationale": "fallback: router LLM unavailable",
    }
    if not settings.openai_api_key:
        return fallback

    llm = ChatOpenAI(
        model=ROUTER_MODEL,
        temperature=0,
        api_key=settings.openai_api_key,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    user = f"Query: {query}"
    if deal_id:
        user += f"\ndeal_id: {deal_id}"

    try:
        msg = await llm.ainvoke([("system", _system_prompt()), ("user", user)])
        raw = msg.content if isinstance(msg.content, str) else str(msg.content)
        data = json.loads(raw)
    except Exception as exc:
        logger.warning("router-llm-failed: %s", exc)
        return fallback

    mode = data.get("mode")
    if mode not in ("rag", "tools", "rag+tools"):
        logger.warning("router-bad-mode: %r — using fallback", mode)
        return fallback

    return {
        "mode": mode,
        "needs_action": bool(data.get("needs_action", deal_id is not None)),
        "rationale": str(data.get("rationale", ""))[:200],
    }
