"""QS-042 — Synthesizer with hard citation enforcement.

Defence-in-depth against LLM hallucination of source names:
1. The prompt forbids citing anything not in the input (see synthesis.txt).
2. _filter_citations() post-processes the LLM output and STRIPS any
   `[Source: X]` where X doesn't match a provided source verbatim
   (or via a relaxed prefix match).
3. The returned `citations` list contains only sources actually referenced
   in the cleaned answer — guaranteeing inline citations and the bottom
   list always agree.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TypedDict

from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "synthesis.txt"
SYNTH_MODEL = "gpt-4o"
CITATION_RE = re.compile(r"\[Source\s*:\s*([^\]]+?)\]")


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
            f"[CHUNK {i}] source=\"{c.get('source', '?')}\" url={c.get('url', '')}\n"
            f"{c.get('text', '')[:600]}\n"
        )
    return "\n".join(lines)


def _format_tools_data(tools: dict) -> str:
    if not tools or not tools.get("data"):
        return "(aucune donnée live)"
    lines = [f"Tools data:\n{tools.get('data')}"]
    sources = tools.get("sources", [])
    if sources:
        lines.append("Sources Tools (noms à utiliser verbatim si cités):")
        for s in sources:
            lines.append(f'  - "{s.get("name", "?")}" ({s.get("url", "")})')
    return "\n".join(lines)


def _filter_citations(answer: str, valid_sources: set[str]) -> tuple[str, list[str]]:
    """Strip any [Source: X] where X doesn't match a provided source. Returns
    (cleaned_answer, list_of_used_sources) where order is first-cited-first.
    """
    used: list[str] = []
    seen: set[str] = set()
    valid_lower = {s.lower(): s for s in valid_sources}

    def _replace(match: re.Match[str]) -> str:
        cited_raw = match.group(1).strip().strip("\"'")
        # exact match
        if cited_raw in valid_sources:
            if cited_raw not in seen:
                used.append(cited_raw)
                seen.add(cited_raw)
            return f"[Source: {cited_raw}]"
        # case-insensitive exact
        canonical = valid_lower.get(cited_raw.lower())
        if canonical is not None:
            if canonical not in seen:
                used.append(canonical)
                seen.add(canonical)
            return f"[Source: {canonical}]"
        # prefix / containment match (e.g. LLM cited "Wikipédia FR — DPE" instead of full name)
        for src in valid_sources:
            if cited_raw.lower() in src.lower() or src.lower() in cited_raw.lower():
                if src not in seen:
                    used.append(src)
                    seen.add(src)
                return f"[Source: {src}]"
        # no match → drop the bogus citation
        logger.warning("citation-stripped: %r not in valid sources", cited_raw)
        return ""

    cleaned = CITATION_RE.sub(_replace, answer)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;])", r"\1", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    return cleaned, used


def _build_citations_list(
    used_sources: list[str],
    rag_chunks: list[dict],
    tools_sources: list[dict],
) -> list[dict]:
    by_source: dict[str, dict] = {}
    for c in rag_chunks:
        s = c.get("source")
        if s and s in used_sources and s not in by_source:
            by_source[s] = {
                "source": s,
                "url": c.get("url", ""),
                "snippet": c.get("text", "")[:280],
                "score": float(c.get("score") or 0.0),
            }
    for s in tools_sources:
        name = s.get("name") if isinstance(s, dict) else None
        if name and name in used_sources and name not in by_source:
            by_source[name] = {
                "source": name,
                "url": s.get("url", "") if isinstance(s, dict) else "",
                "snippet": (s.get("description") or "")[:280] if isinstance(s, dict) else "",
                "score": 0.0,
            }
    # preserve "first cited" order
    return [by_source[s] for s in used_sources if s in by_source]


async def synthesize(query: str, rag: dict, tools: dict) -> SynthResult:
    rag_chunks = rag.get("chunks", []) if rag else []
    tools_sources = tools.get("sources", []) if tools else []

    valid_sources: set[str] = set()
    for c in rag_chunks:
        if c.get("source"):
            valid_sources.add(c["source"])
    for s in tools_sources:
        name = s.get("name") if isinstance(s, dict) else None
        if name:
            valid_sources.add(name)

    if not valid_sources:
        return {
            "answer": "Sources insuffisantes pour formuler une recommandation.",
            "citations": [],
            "refused": True,
        }

    if not settings.openai_api_key:
        logger.warning("synth-disabled: OPENAI_API_KEY not set")
        return {
            "answer": "Synthèse indisponible (clé OpenAI manquante).",
            "citations": [],
            "refused": True,
        }

    llm = ChatOpenAI(model=SYNTH_MODEL, temperature=0.0, api_key=settings.openai_api_key)
    user = (
        f"QUESTION: {query}\n\n"
        f"=== EXTRAITS RAG ===\n{_format_rag_chunks(rag)}\n\n"
        f"=== DONNÉES LIVE ===\n{_format_tools_data(tools)}\n\n"
        "Rappel: ne cite que les noms de sources fournis ci-dessus, verbatim."
    )

    try:
        msg = await llm.ainvoke([("system", _system_prompt()), ("user", user)])
        raw_answer = msg.content if isinstance(msg.content, str) else str(msg.content)
    except Exception as exc:
        logger.warning("synth-failed: %s", exc)
        return {
            "answer": "Erreur de synthèse — voir les sources brutes.",
            "citations": [],
            "refused": True,
        }

    cleaned_answer, used_sources = _filter_citations(raw_answer, valid_sources)
    citations = _build_citations_list(used_sources, rag_chunks, tools_sources)

    if not used_sources:
        logger.warning("synth-zero-valid-citations: refusing")
        return {
            "answer": "Sources insuffisantes pour formuler une recommandation.",
            "citations": [],
            "refused": True,
        }

    return {
        "answer": cleaned_answer,
        "citations": citations,
        "refused": False,
    }
