# Stack & decisions

The thinking behind each choice. Excerpted from `ARCHITECTURE.md` §10 (decision log) — see the full doc on the repo for context per row.

## Locked-in (from PRD)

| Layer | Choice | Why |
|---|---|---|
| Agent orchestration | **LangGraph** | Required by PRD §8 — graded multi-agent demo |
| RAG framework | LangChain + Qdrant | Qdrant is Docker-native, schema-less, free |
| Open-data | **data.gouv MCP** officiel | Mandatory deliverable in the PRD brief |
| CRM | HubSpot Service Keys | Free-tier compatible CRM API |
| API | FastAPI thin | Only `/query`, `/health` — minimal attack surface |
| CLI | Typer + Rich | Rich gives the routing-trace tree the jury sees |
| Container | Docker Compose | One-host SMB stack |
| Security | `secure` + `slowapi` + Pydantic | Helmet-equivalent + rate-limit + input validation |

## Open decisions resolved during planning

### LLM provider — OpenAI (with Mistral toggle)

Considered:
- **OpenAI** ✅ — best out-of-box, native function calling, ~$10–20 lifetime cost
- Anthropic Claude — strong reasoning, citations native
- **Mistral** — `souveraineté FR / EU` angle, kept as `LLM_PROVIDER=mistral` toggle
- Ollama local — €0 but slow, weaker quality, big Docker image

**Decision**: OpenAI default + Mistral toggle via env var. The "votre data ne sort pas d'Europe" pitch is genuinely valuable for a CGP-targeted product, but ship the demo on quality.

### Embeddings — `text-embedding-3-small`

- 1536-d, $0.02/1M tokens, multilingual (French OK)
- Corpus indexing one-shot cost: ~$0.01
- Open-source alternative: `bge-m3` via sentence-transformers (toggle for full local mode)

### Vector DB — Qdrant

- Free, self-hosted, Docker-native
- Rejected: pgvector (extra Postgres complexity), Pinecone (paid, non-EU)

### Web search — Tavily

- Designed for AI agents (clean snippets, no HTML scraping)
- Free tier 1,000 q/mo
- Rejected: Brave (more setup), DuckDuckGo (lower quality)

### Memory — Redis

Originally planned in-process. Switched to Redis once the 4GB droplet had headroom:
- Tool result cache (DVF 24h, web 1h, INSEE 7d) — saves ~10× on repeat-query costs
- LangChain `RedisCache` for LLM dedup (demo replays cost $0)
- `slowapi` rate-limit backend (cluster-safe with multiple uvicorn workers)
- LangGraph checkpointer (conversation survives `docker compose restart`)

### Observability — Langfuse v2 (self-hosted)

| Option | Tradeoff |
|---|---|
| **Langfuse v2 self-hosted** ✅ | ~2.5GB on the droplet, fits 4GB |
| Langfuse v3 self-hosted ❌ | Needs ClickHouse, ~3.9GB on 4GB = first OOM |
| Langfuse Cloud | Free tier 50k traces/mo — saves RAM, loses self-host pitch |

### Frontend — CLI primary + thin Streamlit

- CLI is the demo surface (routing trace visible)
- Streamlit page (~1h to build) makes jury experience much better than `tail -f`
- Next.js rejected — eats hardening time for marginal demo value

### Hosting — DO Droplet 4GB AMS3

- $24/mo (Basic 4GB)
- AMS3 region: ~25ms latency from Lyon vs ~90ms from NYC3
- $200 GitHub Student credit must be spent before 2026-06-26 expiration

## What we explicitly chose NOT to do (v1)

- **No domain** — droplet IP only. Caddy auto-TLS waits for v2.
- **No DO Spaces** — DVF cache lives on droplet disk (only ~500MB needed).
- **No multi-tenant** — single-tenant deployment, scaling debate deferred.
- **No HubSpot OAuth** — Service Key is enough for v1; OAuth in v2.
- **No Next.js** — Streamlit page is good enough to demo.

## Cost summary

| Item | Cost |
|---|---|
| DO Droplet 4GB (AMS3) | $24/mo |
| OpenAI tokens (lifetime, 44h project) | ~$10–20 |
| HubSpot Free | $0 |
| data.gouv MCP | $0 (public) |
| Tavily | $0 (free tier) |
| Langfuse | $0 (self-hosted) |
| GitHub | $0 |
| **Total recurring** | **~$24/mo** |

Burns ~$24 of the GitHub Student DO credit before June 26 expiration → saves ~$176 from being wasted.
