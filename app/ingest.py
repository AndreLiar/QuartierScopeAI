"""QS-030 + QS-031 + QS-033 — RAG corpus ingestion pipeline.

Reads `data/corpus/sources.yaml`, downloads each source (PDF or HTML),
splits into chunks, embeds with OpenAI `text-embedding-3-small`, upserts
to Qdrant with rich metadata (source name, URL, page, last_updated).

Citation enforcement (QS-032) consumes `metadata.source` + `metadata.url`
from the chunks at retrieval time.

Run: `python -m app.ingest`  (one-shot, idempotent — re-runs replace).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

CORPUS_DIR = Path("data/corpus/raw")
COLLECTION = "quartierscope_corpus"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


# QS-033 — the actual corpus, 11 sources. URLs verified at write-time;
# a few may rot — `python -m app.ingest --skip-broken` swallows fetch errors.
SOURCES: list[dict[str, str]] = [
    {
        "name": "Wikipédia FR — Demande de valeurs foncières (DVF)",
        "url": "https://fr.wikipedia.org/wiki/Demande_de_valeurs_fonci%C3%A8res",
        "kind": "html",
        "category": "methodology",
    },
    {
        "name": "Wikipédia FR — Loi Pinel",
        "url": "https://fr.wikipedia.org/wiki/Dispositif_Pinel",
        "kind": "html",
        "category": "regulation",
    },
    {
        "name": "Wikipédia FR — Location meublée non professionnelle (LMNP)",
        "url": "https://fr.wikipedia.org/wiki/Location_meubl%C3%A9e_non_professionnelle",
        "kind": "html",
        "category": "regulation",
    },
    {
        "name": "Wikipédia FR — Dispositif Denormandie",
        "url": "https://fr.wikipedia.org/wiki/Dispositif_Denormandie",
        "kind": "html",
        "category": "regulation",
    },
    {
        "name": "Wikipédia FR — Diagnostic de performance énergétique (DPE)",
        "url": "https://fr.wikipedia.org/wiki/Diagnostic_de_performance_%C3%A9nerg%C3%A9tique",
        "kind": "html",
        "category": "methodology",
    },
    {
        "name": "Wikipédia FR — Zones tendues",
        "url": "https://fr.wikipedia.org/wiki/Zone_tendue",
        "kind": "html",
        "category": "regulation",
    },
    {
        "name": "Wikipédia FR — Encadrement des loyers en France",
        "url": "https://fr.wikipedia.org/wiki/Encadrement_des_loyers_en_France",
        "kind": "html",
        "category": "regulation",
    },
    {
        "name": "Wikipédia FR — Conseil en gestion de patrimoine",
        "url": "https://fr.wikipedia.org/wiki/Conseil_en_gestion_de_patrimoine",
        "kind": "html",
        "category": "compliance",
    },
    {
        "name": "Wikipédia FR — Conseiller en investissements financiers (CIF)",
        "url": "https://fr.wikipedia.org/wiki/Conseiller_en_investissements_financiers",
        "kind": "html",
        "category": "compliance",
    },
    {
        "name": "Wikipédia FR — Plan de prévention des risques d'inondation (PPRI)",
        "url": "https://fr.wikipedia.org/wiki/Plan_de_pr%C3%A9vention_des_risques_d%27inondation",
        "kind": "html",
        "category": "risk",
    },
    {
        "name": "Wikipédia FR — Marché immobilier français",
        "url": "https://fr.wikipedia.org/wiki/March%C3%A9_immobilier_en_France",
        "kind": "html",
        "category": "methodology",
    },
]


async def _download(source: dict[str, str], skip_broken: bool = False) -> Path | None:
    target = CORPUS_DIR / _slug(source["name"])
    target = target.with_suffix(".pdf" if source["kind"] == "pdf" else ".html")
    if target.exists():
        logger.info("cached: %s", target)
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            r = await client.get(source["url"], headers={"User-Agent": "QuartierScopeAI/0.1 (+research)"})
            r.raise_for_status()
            target.write_bytes(r.content)
            logger.info("downloaded %s -> %s (%d bytes)", source["url"], target, len(r.content))
            return target
    except Exception as exc:
        if skip_broken:
            logger.warning("skip-broken: %s (%s)", source["url"], exc)
            return None
        raise


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")[:80]


def _load(path: Path) -> list[Document]:
    if path.suffix == ".pdf":
        return PyPDFLoader(str(path)).load()
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return [Document(page_content=text, metadata={"source_path": str(path)})]


def _chunk(docs: list[Document], source_meta: dict[str, str]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)
    for c in chunks:
        c.metadata.update(source_meta)
    return chunks


async def _ensure_collection(qdrant: AsyncQdrantClient) -> None:
    collections = await qdrant.get_collections()
    if any(c.name == COLLECTION for c in collections.collections):
        return
    await qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=qmodels.VectorParams(size=EMBED_DIM, distance=qmodels.Distance.COSINE),
    )
    logger.info("created Qdrant collection %r (dim=%d)", COLLECTION, EMBED_DIM)


def _point_id(text: str, source: str) -> str:
    digest = hashlib.sha256(f"{source}:{text}".encode()).digest()[:16]
    return str(uuid.UUID(bytes=digest))


async def ingest(skip_broken: bool = True) -> dict[str, int]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set — cannot embed")

    qdrant = AsyncQdrantClient(url=settings.qdrant_url)
    await _ensure_collection(qdrant)

    embedder = OpenAIEmbeddings(model=EMBED_MODEL, api_key=settings.openai_api_key)

    total_chunks = 0
    total_sources = 0
    for source in SOURCES:
        path = await _download(source, skip_broken=skip_broken)
        if path is None:
            continue
        try:
            docs = _load(path)
        except Exception as exc:
            logger.warning("load-failed: %s (%s)", path, exc)
            continue

        chunks = _chunk(
            docs,
            {
                "source": source["name"],
                "url": source["url"],
                "category": source.get("category", "methodology"),
            },
        )
        if not chunks:
            continue

        texts = [c.page_content for c in chunks]
        vectors: list[list[float]] = await embedder.aembed_documents(texts)

        points = [
            qmodels.PointStruct(
                id=_point_id(c.page_content, source["name"]),
                vector=v,
                payload={"text": c.page_content, **c.metadata},
            )
            for c, v in zip(chunks, vectors, strict=True)
        ]
        await qdrant.upsert(collection_name=COLLECTION, points=points)
        logger.info("upserted %d chunks for %r", len(points), source["name"])
        total_chunks += len(points)
        total_sources += 1

    await qdrant.close()
    return {"sources": total_sources, "chunks": total_chunks}


def main() -> None:
    result = asyncio.run(ingest())
    print(f"\n✓ ingestion complete: {result['sources']} sources, {result['chunks']} chunks")


if __name__ == "__main__":
    main()
