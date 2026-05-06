# Architecture

System design for QuartierScope AI. The full canonical doc lives in [`ARCHITECTURE.md`](https://github.com/AndreLiar/QuartierScopeAI/blob/main/ARCHITECTURE.md) — what follows is the navigable summary.

## Big picture

```
Sarah / Marc (CLI ou Streamlit)
        │
        ▼
   Caddy (TLS / reverse proxy)
        │
        ▼
   FastAPI thin (POST /query)
        │
        ▼
   orchestrator.run(query, history, deal_id)
        │
        ▼
   LangGraph state machine
   ┌────────┬───────────┬──────────────┐
   │ Router │ RAG       │ Tools        │
   │  ↓     │   ↓       │   ↓          │
   │  mode  │ Qdrant    │ data.gouv MCP│
   │ class  │ corpus    │ Cerema DVF    │
   │        │ citations │ Tavily web    │
   │        │           │ HubSpot read  │
   └────────┴─────┬─────┴──────┬───────┘
                  │            │
                  ▼            ▼
              Synthesizer (RAG + Tools, enforces citations)
                  │
                  ▼
              Actions agent (proposes HubSpot writes)
                  │
                  ▼ (only after [y/N] confirm)
              HubSpot MCP / API
```

## The four agents

### 1. Router
- Single LLM call (`gpt-4o-mini`) with constrained JSON output
- Returns `{mode: "rag" | "tools" | "rag+tools", needs_action: bool}`
- Decision rule:
  - Conceptual / methodology → **RAG**
  - Live data / specific commune → **Tools**
  - Mixed → **RAG + Tools** (parallel)
  - `deal_id` present → also Actions agent

### 2. RAG agent
- Qdrant vector DB, OpenAI `text-embedding-3-small` (1536-d)
- Corpus: 11 French sources (ANIL, Notaires de France, Cerema, INSEE, OLAP, ADEME, Banque de France, Service-public, MTE, AMF, ORIAS)
- **Citation enforcement**: refuses to answer if no chunk passes similarity threshold

### 3. Tools agent (read-only)
- `data.gouv MCP` officiel (`mcp.data.gouv.fr/mcp`) — datasets + dataservices discovery
- `dvf.py` — Cerema API discovered via MCP `search_dataservices`, DuckDB fallback over `dvf.csv.gz`
- `web_search.py` — Tavily, with SSRF guard
- `hubspot_mcp.py` (read methods only — `get_contact`, `get_deal`)

### 4. Actions agent (write — confirmation gate)
- HubSpot writes: `create_note`, `update_property`, `create_task`
- **Always two-phase**: propose plan → user confirms → execute
- Disabled at startup if `HUBSPOT_TOKEN` absent

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Orchestration | LangGraph + LangChain |
| LLM | OpenAI `gpt-4o-mini` (router) + `gpt-4o` (synth) — Mistral toggle via env |
| Embeddings | `text-embedding-3-small` |
| Vector DB | Qdrant (Docker) |
| MCP | data.gouv MCP (officiel) + HubSpot Service Keys |
| Cache + state | Redis (LangGraph checkpointer + slowapi rate-limit + LLM cache) |
| API | FastAPI thin (`/query`, `/health`) |
| CLI | Typer + Rich (routing trace) |
| Web demo | Streamlit (1 page calling `/query`) |
| Observability | Langfuse v2 self-hosted |
| Reverse proxy | Caddy (auto-TLS prêt si domaine ajouté) |
| Container | Docker Compose |
| Hosting | DigitalOcean droplet 4GB / 2 vCPU (AMS3) |
| CI/CD | GitHub Actions (rsync + docker compose up) |

## Memory budget on the 4GB droplet

| Service | RAM est. |
|---|---|
| Ubuntu base + Docker daemon | 400 MB |
| Caddy | 50 MB |
| `app` (uvicorn 2 workers + Streamlit) | 500 MB |
| Qdrant | 600 MB |
| Redis (`maxmemory 100mb`) | 150 MB |
| Langfuse Server (Next.js v2) | 400 MB |
| Langfuse Postgres | 400 MB |
| **Used** | **~2.5 GB** |
| **Free margin** | **~1.5 GB** |

## Why Langfuse v2 (not v3)

Langfuse v3 needs ClickHouse (~1.2GB extra) which would put us at ~3.9GB on a 4GB droplet — first traffic spike OOM-kills. v2 is Postgres-only, fits with a comfortable 1.5GB margin, and gives us all the trace UI we need for the demo.

[→ Full ARCHITECTURE.md with C4 diagrams + sequence flows](https://github.com/AndreLiar/QuartierScopeAI/blob/main/ARCHITECTURE.md)
