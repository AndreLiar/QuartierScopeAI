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
from app.observability import trace_config

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "synthesis.txt"
SYNTH_MODEL = "gpt-4o"
CITATION_RE = re.compile(r"\[Source\s*:\s*([^\]]+?)\]")


class SynthResult(TypedDict):
    answer: str
    citations: list[dict]
    refused: bool


_BASE_PROMPT_CACHE: str | None = None


def _system_prompt() -> str:
    global _BASE_PROMPT_CACHE
    if _BASE_PROMPT_CACHE is None:
        _BASE_PROMPT_CACHE = PROMPT_PATH.read_text(encoding="utf-8")
    return _BASE_PROMPT_CACHE


# When chunks of a given category are present, the LLM is REQUIRED to include
# the matching section. Avoids the failure mode where multi-query retrieval
# surfaces PPRI chunks but the LLM skips the risk dimension.
SECTION_REQUIREMENTS: dict[str, str] = {
    "regulation": (
        "**Régulation / dispositif fiscal** — cite la régulation pertinente "
        "(Pinel, LMNP, Denormandie, encadrement des loyers, zones tendues)"
    ),
    "risk": (
        "**Risques géographiques** — mentionne explicitement si la commune est "
        "concernée par un PPRI (Plan de Prévention des Risques d'Inondation), "
        "zones inondables ou autres risques naturels. Ne pas omettre cette section "
        "si des extraits de cette catégorie sont fournis."
    ),
    "methodology": (
        "**Méthodologie d'évaluation** — explicite le calcul de rentabilité "
        "(brute / nette / nette nette), critères de scoring quartier, ou indicateurs DVF"
    ),
    "compliance": (
        "**Conformité CGP/CIF** — devoir de conseil, Lettre de Mission AMF, "
        "obligations ORIAS"
    ),
    "pricing": (
        "**Données de marché** — prix au m², transactions récentes DVF, "
        "écart au médian si disponible"
    ),
}


def _build_dynamic_prompt(chunks: list[dict]) -> str:
    categories = sorted({c.get("category") or "" for c in chunks})
    relevant = [c for c in categories if c in SECTION_REQUIREMENTS]
    if not relevant:
        return _system_prompt()

    addendum = (
        "\n\n=== SECTIONS OBLIGATOIRES POUR CETTE REQUÊTE ===\n"
        "Au vu des extraits fournis, ta réponse DOIT comporter une section abordant "
        "explicitement CHACUN des points suivants. Pour chaque section, cite au "
        "moins un [Source: ...] issu d'extraits de la catégorie correspondante.\n\n"
    )
    for cat in relevant:
        addendum += f"- {SECTION_REQUIREMENTS[cat]}\n"
    addendum += (
        "\nN'omets AUCUNE section ci-dessus. Si tu n'as pas d'information sur "
        "un point, dis-le explicitement plutôt que de l'omettre."
    )
    return _system_prompt() + addendum


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


def _tokenize(s: str) -> set[str]:
    tokens = re.split(r"[\s\-—()/,]+", s.lower())
    return {t for t in tokens if len(t) > 2}


def _filter_citations(answer: str, valid_sources: set[str]) -> tuple[str, list[str]]:
    """Strip any [Source: X] where X doesn't match a provided source. Returns
    (cleaned_answer, list_of_used_sources) where order is first-cited-first.

    Matching strategy (in order):
    1. exact match
    2. case-insensitive exact
    3. token-overlap: ≥50% of cited tokens (len>2) appear in a valid source
    """
    used: list[str] = []
    seen: set[str] = set()
    valid_lower = {s.lower(): s for s in valid_sources}
    valid_tokens = {src: _tokenize(src) for src in valid_sources}

    def _replace(match: re.Match[str]) -> str:
        cited_raw = match.group(1).strip().strip("\"'")
        if cited_raw in valid_sources:
            target = cited_raw
        elif cited_raw.lower() in valid_lower:
            target = valid_lower[cited_raw.lower()]
        else:
            cited_toks = _tokenize(cited_raw)
            best_match: str | None = None
            best_overlap = 0
            for src, toks in valid_tokens.items():
                overlap = len(cited_toks & toks)
                threshold = max(1, len(cited_toks) // 2)
                if overlap > best_overlap and overlap >= threshold:
                    best_overlap = overlap
                    best_match = src
            if best_match is None:
                logger.warning("citation-stripped: %r not in valid sources", cited_raw)
                return ""
            target = best_match

        if target not in seen:
            used.append(target)
            seen.add(target)
        return f"[Source: {target}]"

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

    system_prompt = _build_dynamic_prompt(rag_chunks)
    try:
        msg = await llm.ainvoke(
            [("system", system_prompt), ("user", user)],
            config=trace_config(
                name="synthesizer",
                metadata={
                    "rag_chunks": len(rag_chunks),
                    "tools_sources": len(tools_sources),
                    "categories": sorted({c.get("category") for c in rag_chunks if c.get("category")}),
                },
            ),
        )
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
