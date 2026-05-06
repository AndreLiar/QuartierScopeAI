"""Synthesizer — combine RAG + Tools, enforce citations. Wire in QS-042."""


async def synthesize(rag: dict, tools: dict) -> dict:
    return {"answer": "", "citations": []}
