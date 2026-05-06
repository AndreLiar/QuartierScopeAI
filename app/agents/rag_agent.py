"""RAG agent — retrieve from Qdrant, refuse if no source. Wire in QS-032."""

from typing import TypedDict


class RagResult(TypedDict):
    chunks: list[dict]
    answer: str
    citations: list[dict]


async def retrieve(query: str, k: int = 5) -> RagResult:
    return {"chunks": [], "answer": "", "citations": []}
