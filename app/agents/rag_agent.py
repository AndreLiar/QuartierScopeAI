"""QS-032 — RAG retrieval with citation enforcement.

Retrieves top-k chunks from Qdrant, applies a similarity threshold, and
returns both the chunks AND a list of citations. The synthesizer (QS-042)
is hard-coded to refuse if `citations` is empty.
"""

from __future__ import annotations

import logging
from typing import TypedDict

from langchain_openai import OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient

from app.config import settings
from app.ingest import COLLECTION, EMBED_MODEL

logger = logging.getLogger(__name__)

DEFAULT_K = 5
SIMILARITY_THRESHOLD = 0.30


class Citation(TypedDict):
    source: str
    url: str
    snippet: str
    score: float


class RagResult(TypedDict):
    chunks: list[dict]
    citations: list[Citation]
    refused: bool


async def retrieve(query: str, k: int = DEFAULT_K) -> RagResult:
    if not settings.openai_api_key:
        logger.warning("rag-disabled: OPENAI_API_KEY not set")
        return {"chunks": [], "citations": [], "refused": True}

    embedder = OpenAIEmbeddings(model=EMBED_MODEL, api_key=settings.openai_api_key)
    try:
        qvec = await embedder.aembed_query(query)
    except Exception as exc:
        logger.warning("rag-embed-failed: %s", exc)
        return {"chunks": [], "citations": [], "refused": True}

    qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        hits = await qdrant.search(
            collection_name=COLLECTION,
            query_vector=qvec,
            limit=k,
            with_payload=True,
            score_threshold=SIMILARITY_THRESHOLD,
        )
    except Exception as exc:
        logger.warning("rag-search-failed: %s", exc)
        await qdrant.close()
        return {"chunks": [], "citations": [], "refused": True}
    finally:
        await qdrant.close()

    if not hits:
        logger.info("rag-no-hit: refusing per citation policy (PRD §13.2)")
        return {"chunks": [], "citations": [], "refused": True}

    chunks: list[dict] = []
    citations: list[Citation] = []
    seen_sources: set[str] = set()
    for h in hits:
        payload = h.payload or {}
        text = payload.get("text", "")
        source = payload.get("source", "unknown")
        url = payload.get("url", "")
        chunks.append(
            {
                "text": text,
                "source": source,
                "url": url,
                "score": h.score,
                "category": payload.get("category"),
            }
        )
        if source not in seen_sources:
            citations.append(
                {
                    "source": source,
                    "url": url,
                    "snippet": text[:280],
                    "score": h.score,
                }
            )
            seen_sources.add(source)

    return {"chunks": chunks, "citations": citations, "refused": False}
