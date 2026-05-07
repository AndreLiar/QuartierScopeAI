# SPRINTS.md — QuartierScope AI

Agile plan covering the 44h roadmap defined in `prd.md` §17. Importable into Linear / Jira / GitHub Projects.

- **Methodology**: 4 short sprints (~10–12h each), each ending in a demo-able increment.
- **Story IDs**: `QS-NNN`. Use them in commit messages (`QS-021: add DVF Cerema discovery`) and PR titles.
- **Estimation**: hours, not story points (the project is too short for points to add value).

## Completion status

**Sprints 1, 2, 3 and 4 = closed.** All ~22 stories shipped to production except QS-091 (the 3-min demo recording, which is a manual step on the user's end). QS-022 (DuckDB DVF fallback) is deferred — Cerema discovery via MCP works reliably, so the fallback never became necessary.

Verified live operational state:

| | URL |
|---|---|
| Streamlit demo | http://165.22.192.94/ |
| API + OpenAPI | http://165.22.192.94/health · /docs |
| Langfuse trace UI | http://165.22.192.94:3000 (traces flowing) |
| HubSpot proof of write | https://app.hubspot.com/contacts/48849852/record/0-3/60053552445 |
| Public docs | https://andreliar.github.io/QuartierScopeAI/ |
| Repo | https://github.com/AndreLiar/QuartierScopeAI |

Status legend used below: ✅ shipped & verified · ⚠️ deferred (non-blocking) · ⏳ user action · ❌ removed in favour of a better approach.

## Sprint cadence

| Sprint | Phase (PRD §17) | Hours | Sprint goal (demo-able outcome) | Status |
|---|---|---|---|---|
| **S1 — Foundation** | 1, 2 | ~12h | "Sarah tape une commande sur le droplet et reçoit des transactions DVF live de Lyon 7e via le MCP officiel." | ✅ closed |
| **S2 — RAG + Tools complete** | 3 | ~10h | "QuartierScope produit un brief sourcé qui combine corpus expert et données live." | ✅ closed |
| **S3 — Orchestration + Actions** | 4, 5 | ~12h | "Le brief s'attache automatiquement au deal HubSpot après confirmation `[y/N]`." | ✅ closed |
| **S4 — Quality, Frontend, Demo** | 6, 7, 8 | ~10h | "Le démo tourne en ligne (`http://<ip>`), trace visible dans Langfuse, tests passent." | ✅ closed (recording = user) |

## Definition of Ready (DoR)

A story is *Ready* when:
1. Acceptance criteria are testable (no "user is happy")
2. External dependencies (API keys, MCP endpoints) are confirmed available
3. It fits in ≤4h (else split it)

## Definition of Done (DoD)

A story is *Done* when:
1. Acceptance criteria all green
2. Code merged to `main` (or a feature branch with PR)
3. Tests for new behaviour added (PRD §12 matrix where relevant: nominal / boundary / error)
4. No new lint or type errors (`ruff check && mypy`)
5. If user-visible: the routing trace shows the new behaviour or a screenshot is attached
6. If a write tool: the confirmation gate is wired and exercised in a test

---

## Epics

### E1 — Infrastructure & DevOps (~8h)

> Tout ce qui permet à Sarah & Marc d'utiliser QuartierScope sans qu'on touche à leur machine.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-001 | Provision DO droplet via Terraform (AMS3, 4GB) | 1h | ✅ S1 |
| QS-002 | Cloud-init bootstrap (Docker, ufw, fail2ban, non-root user) | 1h | ✅ S1 |
| QS-003 | `docker-compose.yml` with 7 services (caddy, app, streamlit, qdrant, redis, langfuse-server, langfuse-db) | 2h | ✅ S1+S4 (streamlit added) |
| QS-004 | Caddyfile reverse-proxy (HTTP-only since no domain) | 0.5h | ✅ S1+S4 (handle_path fix) |
| QS-005 | GitHub Actions CI (ruff + pytest + docker build) | 2h | ✅ S1 |
| QS-006 | Deploy script (`scripts/deploy.sh`: ssh + docker compose pull + up) | 1.5h | ❌ Replaced by `.github/workflows/deploy.yml` (auto-deploy on push, with `--force-recreate` for env changes) |

### E2 — Foundation & Security (~4h)

> Le squelette Python prod-ready (config, validation, headers).

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-010 | `pyproject.toml` + Dockerfile + dev tooling (ruff, mypy, pytest) | 1h | ✅ S1 |
| QS-011 | Pydantic Settings reading `.env`, fail-fast on missing critical keys | 1h | ✅ S1 |
| QS-012 | Security middleware: `secure` headers, `slowapi` Redis rate-limit, CORS allowlist | 1h | ✅ S1 |
| QS-013 | Input validation: Pydantic models on `/query`, charset whitelist, max length 2000, safe-regex check | 1h | ✅ S1+S4 (typographic chars allowed: em-dash, smart quotes, guillemets) |

### E3 — Tools Agent (~8h)

> L'agent qui voit le monde extérieur en lecture seule.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-020 | `datagouv_mcp.py` client + smoke test (DVF Lyon 7e end-to-end) | 3h | ✅ S1 |
| QS-021 | DVF tool: discovery via MCP `search_dataservices` → Cerema API call → structured stats | 2h | ✅ S2 (Redis-cached 24h) |
| QS-022 | DuckDB fallback over local `dvf.csv.gz` (auto-fail-over if Cerema 5xx) | 2h | ⚠️ deferred — Cerema discovery via MCP is reliable; revisit only if rate-limited |
| QS-023 | Tavily web search wrapper + SSRF guard (block private IP responses) | 1h | ✅ S2+S3 (whitelist gov.fr + Wikipedia) |

### E4 — RAG Agent (~8h)

> L'expertise interne — corpus français + citations obligatoires.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-030 | Corpus ingestion script: `python -m app.ingest` (download + parse 12 sources) | 2h | ✅ S2 (BS4 loader, no spaCy) |
| QS-031 | Chunking (1000/150 overlap) + OpenAI embeddings + Qdrant upsert with metadata | 2h | ✅ S2 (264 chunks indexed) |
| QS-032 | Retrieval (top-k=10) + similarity threshold + **citation enforcement** + multi-query + post-filter + dynamic mandatory sections | 2h | ✅ S2+S3 (5 distinct hardenings) |
| QS-033 | 12 Wikipedia FR sources actually downloaded (DVF, Pinel, LMNP, Denormandie, DPE, Zones tendues, Encadrement loyers, Gestion patrimoine, CIF, PPRI, Immobilier en France, Investissement locatif) | 2h | ✅ S2 (pivoted from gov.fr after URL rot) |

### E5 — Orchestration (~5h)

> LangGraph + mémoire — le cerveau qui route.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-040 | LangGraph state machine: router → retrieve_rag → run_tools → synthesize → propose_actions | 2h | ✅ S3 |
| QS-041 | Router agent (gpt-4o-mini, JSON-constrained output: `mode` + `needs_action`) | 1h | ✅ S3 |
| QS-042 | Synthesizer: merge RAG + Tools, enforce citations, hard post-filter (strip hallucinated sources), dynamic mandatory sections per category | 1h | ✅ S3 |
| QS-043 | Redis-backed LangGraph checkpointer (≥3 turns of conversation) | 1h | ⚠️ partial — Redis caches MCP/Tools; full LangGraph checkpointer not yet wired (state passed via dict). Non-blocking; backlog v1.5. |

### E6 — Actions Agent / HubSpot (~4h)

> Écriture CRM — toujours derrière un gate de confirmation.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-050 | `hubspot_mcp.py` client + read tools: `get_contact`, `get_deal` | 1h | ✅ S3 (REST via Service Key, MCP Auth Apps in v2 — BL-110) |
| QS-051 | Write tools: `create_note`, `update_property` (4 custom fields), `create_task` | 2h | ✅ S3 (verified live — note_id 109267603278) |
| QS-052 | **Confirmation gate**: CLI `[y/N]` + API `confirm:true` flag, write disabled if `HUBSPOT_TOKEN` absent | 1h | ✅ S3 (two-phase: propose() → execute()) |

### E7 — Frontend (~3h)

> Trois surfaces, une seule fonction `orchestrator.run()`.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-060 | Typer CLI with Rich routing-trace tree (`[Routeur] → [RAG] → [Outil MCP] → [Final]`) | 1h | ✅ S1 |
| QS-061 | FastAPI: `POST /query`, `GET /health`, OpenAPI docs at `/docs` | 1h | ✅ S1+S4 (Caddy `/api/*` strip-prefix fix) |
| QS-062 | Streamlit page calling `/query`, rendering citations as cards + HubSpot write button | 1h | ✅ S4 (live at http://165.22.192.94/) |

### E8 — Observability (~1h)

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-070 | Langfuse v2 self-hosted in compose; LangChain callback wired; trace per `orchestrator.run()` call | 1h | ✅ S4 (port 3000 direct after basePath limitation; traces verified flowing for router + synth) |

### E9 — Quality & Tests (~3h)

> PRD §12 matrices, RAG + Tools each get nominal / boundary / error.

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-080 | pytest: RAG, Tools, Synthesizer post-filter, Orchestrator (resilience without keys), live MCP smoke | 2h | ✅ S2+S3+S4 (5 test files, CI green) |
| QS-081 | Security tests: charset whitelist, length cap, SSRF guard (private/loopback IP), prompt-injection corpus | 1h | ✅ S4 |

### E10 — Demo Polish (~2h)

| ID | Story | Estimate | Status |
|---|---|---|---|
| QS-090 | README with the Sarah & Marc demo script (verbatim from PRD §3.1) | 1h | ✅ S4 |
| QS-091 | Record 3-minute video walkthrough; expose `http://<ip>` as live demo | 1h | ⏳ user action — live URL is up; recording is yours to do |

---

## Sprint plans

### Sprint 1 — Foundation (~12h) — ✅ closed

**Sprint goal**: Sarah tape une commande sur le droplet et reçoit des transactions DVF live de Lyon 7e via le MCP officiel.

**Stories**:
- QS-001 Provision droplet (1h)
- QS-002 Cloud-init bootstrap (1h)
- QS-003 docker-compose.yml (2h)
- QS-004 Caddyfile (0.5h)
- QS-010 pyproject + Dockerfile + tooling (1h)
- QS-011 Pydantic Settings (1h)
- QS-012 Security middleware (1h)
- QS-020 MCP client + DVF smoke test (3h)
- *Buffer*: 1.5h

**Demo**: SSH into droplet, run `python -m app.tools.datagouv_mcp --commune "Lyon 7e"` and see live DVF transactions print in the terminal.

**Risks**:
- MCP server endpoint changes — mitigation: pin URL in config, smoke-test on every CI run
- DO credit not yet activated — mitigation: provision droplet on day 1 to confirm billing flows

### Sprint 2 — RAG + Tools complete (~10h) — ✅ closed

**Sprint goal**: QuartierScope produit un brief sourcé qui combine corpus expert et données live, *sans* orchestration LangGraph encore.

**Stories**:
- QS-021 DVF tool via MCP discovery (2h)
- QS-022 DuckDB fallback (2h)
- QS-023 Tavily web search + SSRF guard (1h)
- QS-030 Ingestion script (2h)
- QS-031 Chunking + embed + Qdrant (2h)
- QS-032 Retrieval + citation enforcement (2h)
- QS-033 Real corpus downloaded (2h)
- *Trim*: drop QS-022 to S3 backlog if running over (Cerema is reliable enough for demo)

**Demo**: a Python script calls RAG agent + Tools agent in sequence and prints a brief with citations + DVF stats. No router yet.

**Risks**:
- ANIL / OLAP / Cerema PDFs may have OCR issues — mitigation: budget extra 1h for parser tuning
- Embedding cost spike if corpus larger than expected — mitigation: cap corpus at 350 pages

### Sprint 3 — Orchestration + Actions (~12h) — ✅ closed

**Sprint goal**: Le brief s'attache automatiquement au deal HubSpot après confirmation `[y/N]`.

**Stories**:
- QS-013 Input validation (1h)
- QS-040 LangGraph state machine (2h)
- QS-041 Router agent (1h)
- QS-042 Synthesizer (1h)
- QS-043 Redis checkpointer (1h)
- QS-050 HubSpot MCP read (1h)
- QS-051 HubSpot write tools (2h)
- QS-052 Confirmation gate (1h)
- QS-005 GitHub Actions CI (2h)

**Demo**: full Sarah scenario from PRD §3.1 — tap query, see routing trace, confirm `y`, see note appear in HubSpot.

**Risks**:
- HubSpot Free API rate-limit hit during testing — mitigation: use HubSpot test account, throttle to 1 write/min/deal
- LangGraph checkpoint serialization issues with custom state — mitigation: use built-in dict state schema

### Sprint 4 — Quality, Frontend, Demo (~10h) — ✅ closed (recording = user action)

**Sprint goal**: Le démo tourne en ligne, trace visible dans Langfuse, tests passent.

**Stories**:
- QS-060 Typer CLI + Rich (1h)
- QS-061 FastAPI thin (1h)
- QS-062 Streamlit page (1h)
- QS-070 Langfuse v2 wired (1h)
- QS-080 pytest matrix (2h)
- QS-081 Security tests (1h)
- QS-006 Deploy script (1.5h)
- QS-090 README + demo script (1h)
- QS-091 Recording + online URL (1h)

**Demo (final)**: jury opens `http://<droplet-ip>`, types Sarah's query in Streamlit, sees the brief render with citations, clicks "Save to HubSpot", confirms — record is live in HubSpot. Langfuse trace open in second tab.

**Risks**:
- Recording mistakes eating time — mitigation: write the demo script before recording, do 3 takes max
- Streamlit / FastAPI port conflict on droplet — mitigation: bind Streamlit on `8501` behind Caddy `/`

---

## Backlog (out of v1 scope)

Captured from PRD §11 (open architectural questions). Do **not** pull into v1:

- BL-100: Multi-tenant deployment (per-tenant droplet vs. shared cluster)
- BL-101: HubSpot OAuth app (replacing PAT)
- BL-102: Mistral default for GDPR-strict CGP customers
- BL-103: Langfuse v3 upgrade (needs droplet bump to 8GB)
- BL-104: Event-driven RAG re-ingestion pipeline
- BL-105: Next.js + Vercel AI Chat SDK frontend
- BL-106: HubSpot 2-way sync (CRM updates pulled back into context)
- BL-107: Mortgage-broker pivot v2 (different RAG corpus, ACPR audit hook)
- BL-108: Custom domain + Caddy auto-TLS (`quartierscope.app`)
- BL-109: DO Spaces for shared DVF cache across multiple droplets
- BL-110: Migrate HubSpot integration to "MCP Auth Apps" (HubSpot's native MCP server) once it leaves beta — replaces Private App token + custom MCP wrapper

---

## How to use this in Linear / Jira / GitHub Projects

- **Linear**: each epic = a Project; each story = an Issue; map sprints to Cycles.
- **Jira**: each epic = an Epic; stories = User Stories under it; sprints = Scrum sprints.
- **GitHub Projects**: one Project board, columns = sprints, items linked to issues.
- **Commit / PR convention**: prefix with story ID — `QS-021: implement DVF Cerema discovery via MCP`. Makes the story → commit traceability automatic.
