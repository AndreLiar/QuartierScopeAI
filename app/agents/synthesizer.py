"""QS-042 — Synthesizer: combine RAG + Tools, enforce citations.

Refuses (returns answer="" + refused=True) if BOTH the RAG agent and the
Tools agent yielded no usable sources. The synthesis prompt is hard-coded
to omit any factual claim that lacks a citation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TypedDict

from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "synthesis.txt"
SYNTH_MODEL = "gpt-4o"


class SynthResult(TypedDict):
    answer: str
    citations: list[dict]
    refused: bool


def _system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _format_rag_chunks(rag: dict) -> str:
    chunks = rag.get("chunks", [])
    if not chunks:
        return "(aucun extrait RAG)"
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(
            f"[CHUNK {i}] source={c.get('source', '?')} url={c.get('url', '')}\n"
            f"{c.get('text', '')[:600]}\n"
        )
    return "\n".join(lines)


def _format_tools_data(tools: dict) -> str:
    if not tools or not tools.get("data"):
        return "(aucune donnée live)"
    lines = [f"Tools data:\n{tools.get('data')}"]
    sources = tools.get("sources", [])
    if sources:
        lines.append("Sources Tools:")
        for s in sources:
            lines.append(f"  - {s.get('name', '?')} ({s.get('url', '')})")
    return "\n".join(lines)


async def synthesize(query: str, rag: dict, tools: dict) -> SynthResult:
    rag_citations = rag.get("citations", []) if rag else []
    tools_sources = tools.get("sources", []) if tools else []

    if not rag_citations and not tools_sources:
        return {
            "answer": "Sources insuffisantes pour formuler une recommandation.",
            "citations": [],
            "refused": True,
        }

    if not settings.openai_api_key:
        logger.warning("synth-disabled: OPENAI_API_KEY not set")
        return {
            "answer": "Synthèse indisponible (clé OpenAI manquante).",
            "citations": rag_citations,
            "refused": True,
        }

    llm = ChatOpenAI(model=SYNTH_MODEL, temperature=0.2, api_key=settings.openai_api_key)
    user = (
        f"QUESTION: {query}\n\n"
        f"=== EXTRAITS RAG ===\n{_format_rag_chunks(rag)}\n\n"
        f"=== DONNÉES LIVE ===\n{_format_tools_data(tools)}\n"
    )

    try:
        msg = await llm.ainvoke([("system", _system_prompt()), ("user", user)])
        answer = msg.content if isinstance(msg.content, str) else str(msg.content)
    except Exception as exc:
        logger.warning("synth-failed: %s", exc)
        return {
            "answer": "Erreur de synthèse — voir les sources brutes.",
            "citations": rag_citations,
            "refused": True,
        }

    return {
        "answer": answer,
        "citations": rag_citations,
        "refused": False,
    }
