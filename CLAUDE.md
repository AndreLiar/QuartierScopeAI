# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

QuartierScope AI is a **shipped, operational** multi-agent AI copilot for independent French CGP firms. v1 (Sprints 1–4, ~44h) is in production at http://165.22.192.94/. v1.5 + v2 roadmap (~58h, Sprints 5–9) is documented in [SPRINTS.md](./SPRINTS.md) but not yet built.

| Surface | URL |
|---|---|
| Streamlit demo | http://165.22.192.94/ |
| FastAPI / OpenAPI | http://165.22.192.94/health · /docs |
| Langfuse traces | http://165.22.192.94:3000 |
| Public docs (VitePress) | https://andreliar.github.io/QuartierScopeAI/ |
| Repo (public) | https://github.com/AndreLiar/QuartierScopeAI |

## Canonical docs (read these first when context is missing)

- **`prd.md`** — what & why, ICP (CGP indé 2-pers, Sarah & Marc), the 2-sentence pitch, security risk matrix (§13), test matrices contract (§12)
- **`ARCHITECTURE.md`** — full C4 diagrams, sequence flows, deployment topology, decision log
- **`SPRINTS.md`** — agile plan, story IDs `QS-NNN`, status badges, v1.5/v2 roadmap
- **`docs/journey.md`** — chronological setup story including every dead-end (HubSpot UI maze, Terraform SSH-key, secure API change, Qdrant version drift, Langfuse env propagation, rubric self-evaluation closure)
- **`docs/test-matrix.md`** — formal nominal/limite/erreur tables mapped to actual pytest functions

When adding code, update whichever docs are affected.

## Common commands

```bash
# Local dev (without Docker)
uv pip install -e ".[dev]"
python -m app smoke                                            # data.gouv MCP smoke test
python -m app dvf 69387 --from 2024                            # DVF discovery via MCP
python -m app rag "Comment scorer un quartier locatif ?"       # RAG retrieval only
python -m app web "tension locative Lyon 7e"                   # Tavily search only
python -m app query "Lyon 7e LMNP" --deal <hubspot-deal-id>    # full multi-agent flow
python -m app query "approfondis ce point" --new               # --new resets session memory
python -m app ingest-corpus                                    # one-shot RAG ingestion

# Tests
pytest -v                                                      # unit + resilience tests
QS_INTEGRATION=1 pytest -v                                     # also run live MCP / Qdrant / OpenAI tests
pytest tests/test_synthesizer.py -v                            # single file
pytest tests/test_memory.py::test_router_includes_history_in_prompt -v  # single test

# Lint
ruff check app tests
mypy app  # advisory; not blocking in CI

# Docker (production-equivalent)
docker compose up -d --build
docker compose exec app python -m app.ingest                   # ingest on droplet
docker compose exec -T app python -m app query "..."           # run via container

# On the droplet (SSH)
ssh -i ~/.ssh/do_ed25519 quartierscope@165.22.192.94
cd ~/quartierscope && docker compose ps                        # service health

# Deploy
git push origin main                                           # auto-triggers CI + Deploy + Docs workflows
gh run list --repo AndreLiar/QuartierScopeAI --limit 5         # check status

# Terraform (infra)
cd terraform/
TF_VAR_do_token=$DO_TOKEN terraform apply
```

## Architecture (operational reality)

LangGraph state machine with **4 cooperating agents**:

```
orchestrator.run(query, history, deal_id, confirm)
   │
   ├─► Router (gpt-4o-mini)         — classifies {mode, needs_action, rationale}
   ├─► RAG agent (Qdrant 264 chunks) — multi-query + post-filter + dynamic mandatory sections
   ├─► Tools agent (read-only)      — data.gouv MCP, DVF Cerema, Tavily web (whitelisted), HubSpot read
   ├─► Synthesizer (gpt-4o)         — combines RAG+Tools, enforces citations
   └─► Actions agent (write)        — HubSpot writes, ALWAYS behind [y/N] / confirm:true gate
```

Two surfaces, one logic: CLI (`app/cli.py`) and FastAPI (`app/api.py`) both call `orchestrator.run()`. Streamlit (`app/streamlit_app.py`) calls FastAPI from inside the same container.

## Hard rules / non-obvious invariants

These have been violated and re-imposed multiple times — keep them in mind:

1. **Citations are mandatory.** Synth refuses if RAG and Tools both yielded zero sources. Citation post-filter (`_filter_citations`) strips any `[Source: X]` where `X` doesn't match a verbatim/fuzzy-token-overlap source name from the input — silently drops hallucinated names like `[Source: Buddey]`. **Never bypass the post-filter.**
2. **MCP is the mandatory data path.** Don't add direct HTTP to data.gouv.fr — go through the official MCP server at `mcp.data.gouv.fr/mcp` (Tabular API has 410'd on DVF; use `search_dataservices` → Cerema flow).
3. **Read/write tool split.** Reads live in Tools agent, writes in Actions agent. Never let a write tool execute without explicit user confirmation (CLI `[y/N]` or API `confirm: true`).
4. **Memory is wired in prompts**, not just plumbing. Both router and synth inject the last 6 turns under `=== HISTORIQUE CONVERSATION ===`. Don't add a third agent without doing the same — follow-ups must work.
5. **HubSpot Free constraints (PRD §3.2)** — non-negotiable: 1 deal pipeline (use existing), no auto-creating contacts (1k cap), 4 custom deal properties max (`qs_*`), email send disabled by default, AI is not a CRM user.
6. **Tavily is whitelisted.** `include_domains` restricts results to gov.fr, Wikipedia, ANIL, AMF, Cerema, Notaires, INSEE, ADEME, Banque de France, ORIAS — no commercial real-estate sites in citations (compliance reason for AMF Lettre de Mission).
7. **CLI is the demo surface, Streamlit is the polished surface, FastAPI is the API.** All three call `orchestrator.run()`. Don't duplicate logic.
8. **Synth has dynamic mandatory sections.** Categories (`regulation`, `risk`, `methodology`, `compliance`, `pricing`) detected in retrieved chunks are forced into the synth prompt as required output sections. PPRI flood risk surfaces because of this — don't break it.

## ICP framing (locked, don't drift)

**Sarah & Marc** — co-fondateurs cabinet CGP indépendant 2 personnes à Lyon. ORIAS-CIF, AMF-supervised, specialised in rental investment (Pinel/LMNP/Denormandie). 12 active files capped by bandwidth, target 25 with QuartierScope. Tickets €200k–500k.

**Compliance hook = AMF Lettre de Mission** (devoir de conseil sourcé). Not ACPR.

**Don't drift to**: mortgage brokers, real-estate agents, B2C, big CGP networks. The PRD pivoted from courtier crédit immo to CGP indé after forum research showed the 2h-on-quartier pain belongs to CGPs.

## Conventions

- **Commit messages**: prefix with story ID — `QS-021: implement DVF Cerema discovery via MCP`. Free-form titles (no co-author trailers).
- **Branch model**: trunk-based. Push to `main` triggers CI + Deploy + Docs workflows in parallel via path-scoped triggers (changes under `docs/**` only build the docs site, etc.).
- **Test matrix**: any new agent / tool / write path needs nominal + limite + erreur cases, mapped from `docs/test-matrix.md`.
- **Resilience pattern**: every external call wrapped in `try/except` with graceful default (e.g. RAG returns `refused=True` on failure, Tools returns empty data, Actions disabled if token absent). Never let one external failure crash a request.

## Stack snapshot

- Python 3.12 · LangGraph + LangChain · Qdrant (vector, 264 chunks) · Redis (cache + slowapi rate-limit) · Langfuse v2 (self-hosted, port 3000)
- OpenAI `gpt-4o-mini` (router) + `gpt-4o` (synth) · `text-embedding-3-small` (1536-d)
- FastAPI · Typer + Rich CLI · Streamlit UI
- HubSpot Free via Service Keys (beta) — Bearer `pat-na1-…`
- Caddy reverse proxy (HTTP only, no domain) · Docker Compose · DigitalOcean droplet 4GB AMS3 ($24/mo)
- GitHub Actions: 3 workflows (CI, Deploy, Docs) auto-deploy on push to `main`. Deploy uses `--force-recreate` to propagate `.env` changes (lesson from journey Phase 7).

## Things that look like gaps but are intentional

- **No DuckDB DVF fallback** — deferred (QS-022 → QS-121 in v1.5). Cerema discovery via MCP works reliably; the fallback is a v1.5 robustness item.
- **`scoring.py` is stubbed** — full neighborhood score computation is QS-105 in v1.5.
- **No PDF Lettre de Mission generator** — that's the v1.5 deliverable (QS-110 in Sprint 6).
- **No fiscal simulators (Pinel/LMNP €€€)** — Sprint 5 in v1.5. Today the corpus *cites* the rules; v1.5 will *compute* them.
- **No multi-tenant** — Sprint 9 in v2.

If a feature seems missing, check SPRINTS.md before adding — it's likely already planned and budgeted.
