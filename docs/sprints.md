# Sprints, epics & stories

44h of work split into 4 demo-able sprints. Story IDs `QS-NNN` are referenced in commits and PR titles for traceability.

## Sprint cadence

| Sprint | Phase | Hours | Goal (demo-able outcome) |
|---|---|---|---|
| **S1 — Foundation** | 1, 2 | ~12h | "Sarah tape une commande sur le droplet et reçoit du DVF Lyon 7e via le MCP officiel." |
| **S2 — RAG + Tools** | 3 | ~10h | "QuartierScope produit un brief sourcé combinant corpus expert et données live." |
| **S3 — Orchestration + Actions** | 4, 5 | ~12h | "Le brief s'attache au deal HubSpot après confirmation `[y/N]`." |
| **S4 — Quality + Frontend + Demo** | 6, 7, 8 | ~10h | "Le démo tourne en ligne, tracé dans Langfuse, tests passent." |

## Definition of Done

A story is *Done* when:
1. Acceptance criteria all green
2. Code merged to `main` (PR squash-merge)
3. Tests for new behaviour added (PRD §12 matrix where relevant: nominal / boundary / error)
4. No new lint or type errors (`ruff check && mypy`)
5. If user-visible: the routing trace shows the new behaviour or screenshot attached
6. If a write tool: the confirmation gate is wired and exercised in a test

## Epics

### E1 — Infrastructure & DevOps (~8h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-001 | Provision DO droplet via Terraform (AMS3, 4GB) | 1h | S1 ✅ |
| QS-002 | Cloud-init bootstrap (Docker, ufw, fail2ban, non-root user) | 1h | S1 ✅ |
| QS-003 | `docker-compose.yml` with 6 services | 2h | S1 ✅ |
| QS-004 | Caddyfile reverse-proxy (HTTP-only since no domain) | 0.5h | S1 ✅ |
| QS-005 | GitHub Actions CI (ruff + pytest + docker build) | 2h | S1 ✅ (CI) S3 (CI matrix) |
| QS-006 | Deploy script | — | ❌ Killed in favour of GH Actions deploy.yml |

### E2 — Foundation & Security (~4h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-010 | `pyproject.toml` + Dockerfile + dev tooling | 1h | S1 ✅ |
| QS-011 | Pydantic Settings (env loading) | 1h | S1 ✅ |
| QS-012 | Security middleware: `secure` headers, `slowapi`, CORS | 1h | S1 ✅ |
| QS-013 | Input validation (Pydantic + safe-regex check) | 1h | S3 |

### E3 — Tools Agent (~8h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-020 | data.gouv MCP client + smoke test (DVF Lyon 7e) | 3h | S1 ✅ |
| QS-021 | DVF tool: discovery via MCP `search_dataservices` → Cerema | 2h | S2 |
| QS-022 | DuckDB fallback over local `dvf.csv.gz` | 2h | S2 |
| QS-023 | Tavily web search wrapper + SSRF guard | 1h | S2 |

### E4 — RAG Agent (~8h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-030 | Corpus ingestion script: `python -m app.ingest` | 2h | S2 |
| QS-031 | Chunking + OpenAI embeddings + Qdrant upsert | 2h | S2 |
| QS-032 | Retrieval + similarity threshold + citation enforcement | 2h | S2 |
| QS-033 | Real corpus actually downloaded (11 sources) | 2h | S2 |

### E5 — Orchestration (~5h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-040 | LangGraph state machine (router → agents → synth) | 2h | S3 |
| QS-041 | Router agent (gpt-4o-mini classifier) | 1h | S3 |
| QS-042 | Synthesizer (combines RAG + Tools, enforces citations) | 1h | S3 |
| QS-043 | Redis-backed LangGraph checkpointer | 1h | S3 |

### E6 — Actions Agent / HubSpot (~4h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-050 | HubSpot client + read tools | 1h | S3 |
| QS-051 | Write tools (create_note, update_property, create_task) | 2h | S3 |
| QS-052 | Confirmation gate (CLI `[y/N]`, API `confirm:true`) | 1h | S3 |

### E7 — Frontend (~3h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-060 | Typer CLI with Rich routing trace | 1h | S4 |
| QS-061 | FastAPI `/query` + `/health` | 1h | S4 ✅ (skeleton) |
| QS-062 | Streamlit page calling `/query` | 1h | S4 |

### E8 — Observability (~1h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-070 | Langfuse v2 self-hosted + LangChain callback wired | 1h | S4 |

### E9 — Quality (~3h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-080 | pytest suite (RAG + Tools + Actions confirmation) | 2h | S4 |
| QS-081 | Security tests (prompt injection, CORS, SSRF) | 1h | S4 |

### E10 — Demo polish (~2h)

| ID | Story | Estimate | Sprint |
|---|---|---|---|
| QS-090 | README + demo script (Sarah & Marc scenario) | 1h | S4 |
| QS-091 | Recording + online URL | 1h | S4 |

## Backlog (out of v1)

- BL-100 Multi-tenant deployment
- BL-101 HubSpot OAuth (replacing Service Key)
- BL-102 Mistral default for GDPR-strict CGP customers
- BL-103 Langfuse v3 upgrade (needs droplet bump to 8GB)
- BL-104 Event-driven RAG re-ingestion pipeline
- BL-105 Next.js + Vercel AI Chat SDK frontend
- BL-106 HubSpot 2-way sync
- BL-107 Mortgage-broker pivot v2 (different RAG corpus, ACPR audit hook)
- BL-108 Custom domain + Caddy auto-TLS
- BL-109 DO Spaces for shared DVF cache
- BL-110 Migrate to HubSpot MCP Auth Apps once it leaves beta

[→ Full SPRINTS.md](https://github.com/AndreLiar/QuartierScopeAI/blob/main/SPRINTS.md)
