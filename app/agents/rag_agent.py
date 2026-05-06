"""QS-032 — RAG retrieval with citation enforcement + multi-query coverage.

Multi-query: for compound questions ("score de risque ET tension locative"),
embed each sub-query separately and union the top-k results. Avoids the
single-vector compromise that misses one dimension of the user's question.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TypedDict

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient

from app.config import settings
from app.ingest import COLLECTION, EMBED_MODEL

logger = logging.getLogger(__name__)

DEFAULT_K = 10
MULTI_QUERY_K = 5
SIMILARITY_THRESHOLD = 0.30
DECOMPOSE_MODEL = "gpt-4o-mini"

# Cheap heuristic: if the query mentions any 2 of these aspects, decompose.
ASPECT_KEYWORDS: dict[str, list[str]] = {
    "risque": ["risque", "inondable", "inondation", "ppri", "danger"],
    "tension_locative": ["tension", "loyer", "encadrement", "vacance", "demande locative"],
    "rentabilite": ["rentabilité", "rendement", "yield", "lmnp", "pinel", "denormandie"],
    "dpe": ["dpe", "énergie", "passoire", "diagnostic"],
    "pricing": ["prix", "€/m²", "valeur", "dvf", "transaction"],
}


class Citation(TypedDict):
    source: str
    url: str
    snippet: str
    score: float


class RagResult(TypedDict):
    chunks: list[dict]
    citations: list[Citation]
    refused: bool


def _detect_aspects(query: str) -> list[str]:
    q = query.lower()
    detected = []
    for aspect, kws in ASPECT_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", q) for kw in kws):
            detected.append(aspect)
    return detected


async def _decompose(query: str, aspects: list[str]) -> list[str]:
    """Use a small LLM to split a multi-aspect query into focused sub-queries."""
    if not settings.openai_api_key or len(aspects) < 2:
        return []
    llm = ChatOpenAI(
        model=DECOMPOSE_MODEL,
        temperature=0,
        api_key=settings.openai_api_key,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    prompt = (
        "Décompose la question utilisateur en 2-3 sous-questions courtes et indépendantes "
        "qui ciblent chacune un aspect distinct (risque, loyer, rentabilité, DPE, prix). "
        'Réponds en JSON: {"queries": ["...", "..."]}.\n\n'
        f"Question: {query}\n"
        f"Aspects détectés: {aspects}"
    )
    try:
        msg = await llm.ainvoke([("user", prompt)])
        import json

        data = json.loads(msg.content if isinstance(msg.content, str) else str(msg.content))
        return [q for q in data.get("queries", []) if isinstance(q, str)][:3]
    except Exception as exc:
        logger.warning("decompose-failed: %s", exc)
        return []


async def _retrieve_single(
    embedder: OpenAIEmbeddings, qdrant: AsyncQdrantClient, query: str, k: int
) -> list[dict]:
    try:
        qvec = await embedder.aembed_query(query)
        response = await qdrant.query_points(
            collection_name=COLLECTION,
            query=qvec,
            limit=k,
            with_payload=True,
            score_threshold=SIMILARITY_THRESHOLD,
        )
        return [
            {
                "text": (h.payload or {}).get("text", ""),
                "source": (h.payload or {}).get("source", "unknown"),
                "url": (h.payload or {}).get("url", ""),
                "category": (h.payload or {}).get("category"),
                "score": float(h.score),
            }
            for h in response.points
        ]
    except Exception as exc:
        logger.warning("rag-retrieve-single-failed (%r): %s", query, exc)
        return []


async def retrieve(query: str, k: int = DEFAULT_K) -> RagResult:
    if not settings.openai_api_key:
        logger.warning("rag-disabled: OPENAI_API_KEY not set")
        return {"chunks": [], "citations": [], "refused": True}

    embedder = OpenAIEmbeddings(model=EMBED_MODEL, api_key=settings.openai_api_key)
    qdrant = AsyncQdrantClient(url=settings.qdrant_url)

    try:
        aspects = _detect_aspects(query)
        sub_queries: list[str] = []
        if len(aspects) >= 2:
            sub_queries = await _decompose(query, aspects)

        all_queries = [query] + sub_queries
        results_per_query = await asyncio.gather(
            *[
                _retrieve_single(embedder, qdrant, q, MULTI_QUERY_K if sub_queries else k)
                for q in all_queries
            ]
        )
    finally:
        await qdrant.close()

    seen_text: set[str] = set()
    chunks: list[dict] = []
    for results in results_per_query:
        for c in results:
            key = c.get("text", "")[:120]
            if key in seen_text or not key:
                continue
            seen_text.add(key)
            chunks.append(c)

    chunks.sort(key=lambda c: c.get("score", 0.0), reverse=True)

    if not chunks:
        logger.info("rag-no-hit: refusing per citation policy (PRD §13.2)")
        return {"chunks": [], "citations": [], "refused": True}

    citations: list[Citation] = []
    seen_sources: set[str] = set()
    for c in chunks:
        source = c["source"]
        if source in seen_sources:
            continue
        seen_sources.add(source)
        citations.append(
            {
                "source": source,
                "url": c["url"],
                "snippet": c["text"][:280],
                "score": c["score"],
            }
        )

    return {"chunks": chunks, "citations": citations, "refused": False}
