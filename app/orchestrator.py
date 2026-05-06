"""Single entrypoint shared by CLI, FastAPI, and Streamlit.

Wire LangGraph here in QS-040.
"""

from typing import TypedDict


class OrchestratorResult(TypedDict):
    answer: str
    trace: list[dict]
    citations: list[dict]
    proposed_actions: list[dict]


async def run(
    query: str,
    history: list[dict] | None = None,
    deal_id: str | None = None,
) -> OrchestratorResult:
    return {
        "answer": "stub — wire LangGraph in QS-040",
        "trace": [
            {"step": "Routeur", "detail": "stub QS-041"},
            {"step": "RAG", "detail": "stub QS-032"},
            {"step": "Tools", "detail": "stub QS-021"},
        ],
        "citations": [],
        "proposed_actions": [
            {"tool": "hubspot_create_note", "deal_id": deal_id} if deal_id else {}
        ]
        if deal_id
        else [],
    }
