"""Router agent — classifies the query into RAG / Tools / RAG+Tools. Wire in QS-041."""

from typing import Literal, TypedDict


class RouterDecision(TypedDict):
    mode: Literal["rag", "tools", "rag+tools"]
    needs_action: bool
    rationale: str


async def classify(query: str, deal_id: str | None = None) -> RouterDecision:
    return {
        "mode": "rag+tools",
        "needs_action": deal_id is not None,
        "rationale": "stub QS-041",
    }
