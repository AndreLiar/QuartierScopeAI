# QuartierScope AI

> Le coéquipier IA des cabinets CGP indépendants — 2 h de due-diligence quartier compressées en **30 secondes**, attachées au bon deal HubSpot, avec citations exploitables en Lettre de Mission AMF.

[![CI](https://github.com/AndreLiar/QuartierScopeAI/actions/workflows/ci.yml/badge.svg)](https://github.com/AndreLiar/QuartierScopeAI/actions/workflows/ci.yml)
[![Deploy](https://github.com/AndreLiar/QuartierScopeAI/actions/workflows/deploy.yml/badge.svg)](https://github.com/AndreLiar/QuartierScopeAI/actions/workflows/deploy.yml)
[![Docs](https://github.com/AndreLiar/QuartierScopeAI/actions/workflows/docs.yml/badge.svg)](https://andreliar.github.io/QuartierScopeAI/)

---

## Live demo

| Surface | URL |
|---|---|
| Streamlit UI | http://165.22.192.94/ |
| API health | http://165.22.192.94/health |
| OpenAPI docs | http://165.22.192.94/docs |
| Langfuse traces | http://165.22.192.94/langfuse |
| Documentation site | https://andreliar.github.io/QuartierScopeAI/ |

## What it is

A **multi-agent AI copilot** built on **LangGraph** for a 2-person CGP firm advising rental investments (Pinel / LMNP / Denormandie). Single push triggers CI/CD to a DigitalOcean 4 GB droplet running Docker Compose.

```
Sarah types  →  Router (gpt-4o-mini)
                    ↓
                ┌─ RAG agent  (Qdrant 264 chunks, 12 Wikipedia FR sources)
                ├─ Tools agent (data.gouv MCP → Cerema DVF + Tavily web)
                └─ Actions agent (HubSpot writes, behind [y/N] gate)
                    ↓
                Synthesizer (gpt-4o, citation-enforced)
                    ↓
                French CGP brief + clickable sources + HubSpot note
```

## Architecture summary

| Layer | Choice |
|---|---|
| Orchestration | LangGraph + LangChain |
| LLM | OpenAI gpt-4o-mini (router) + gpt-4o (synth) |
| Embeddings | text-embedding-3-small (1536-d) |
| Vector DB | Qdrant |
| Cache + checkpointer | Redis |
| MCP | data.gouv (open-data) + HubSpot (CRM) |
| Web search | Tavily (whitelisted to gov.fr + Wikipedia) |
| API | FastAPI thin (`/query`, `/health`) |
| CLI | Typer + Rich (routing trace) |
| UI | Streamlit |
| Observability | Langfuse v2 self-hosted |
| Reverse proxy | Caddy |
| Container | Docker Compose |
| Hosting | DigitalOcean droplet (Basic 4 GB, AMS3, $24/mo) |
| CI/CD | GitHub Actions auto-deploy on push to main |

## Quick start (local)

```bash
git clone https://github.com/AndreLiar/QuartierScopeAI
cd QuartierScopeAI
cp .env.example .env  # edit OPENAI_API_KEY, TAVILY_API_KEY, HUBSPOT_TOKEN
docker compose up -d
docker compose exec app python -m app.ingest          # one-shot RAG corpus
docker compose exec app python -m app smoke           # MCP connection test
docker compose exec app python -m app rag "Comment scorer un quartier locatif?"
```

## Sarah scenario (the demo)

```bash
docker compose exec app python -m app query \
  "Lyon 7e Guillotière, T2 LMNP 220k pour primo-investisseur — quel score de risque et tension locative ?" \
  --deal <hubspot-deal-id>
```

Expected:
- **Routeur** → mode=rag+tools, action=true (deal_id present)
- **RAG** → ~22 chunks across 7 sources (multi-query expansion: risque + tension + rentabilité)
- **Tools** → DVF discovery via MCP + Tavily on whitelisted domains
- **Synthèse** → French brief, citations cliquables, mandatory sections (régulation / risques / méthodologie / compliance) based on retrieved categories
- **Actions** → "Save to HubSpot? [y/N]" → on `y`, note + custom property update appear on the deal

## Deploy

Every push to `main` triggers GitHub Actions deploy:
1. CI — ruff + pytest
2. Deploy — rsync + `docker compose up -d` on the droplet
3. Docs — VitePress build → GitHub Pages

Secrets needed in GitHub Actions:
- `SSH_PRIVATE_KEY` — private key authorised on the droplet
- `DROPLET_HOST` — public IP of the droplet

## Security highlights (PRD §13)

| Threat | Control | Where |
|---|---|---|
| Prompt injection | Strict system prompts + Pydantic charset whitelist | `app/security.py` + `app/prompts/*.txt` |
| LLM hallucinated source name | Citation post-filter strips bogus `[Source: X]` | `app/agents/synthesizer.py::_filter_citations` |
| Hallucination via missing source | Refuse if no citation passes threshold | RAG + synth refuse paths |
| Unauthorized CRM write | Two-agent split + explicit `[y/N]` gate | `app/agents/actions_agent.py` |
| SSRF via web search | `is_private_or_loopback` filter on Tavily results | `app/security.py` + `app/tools/web_search.py` |
| Commercial sources in compliance brief | Tavily `include_domains` whitelist | `app/tools/web_search.py` |
| API DoS | `slowapi` Redis-backed rate-limit (10 req/min/IP) | `app/api.py` |
| CORS open | Explicit `CORS_ALLOWED_ORIGINS` allowlist | `app/api.py` |
| HTTP header gaps | `secure` package middleware | `app/api.py::add_secure_headers` |

## Documentation

Full architecture, sprint plan, and the setup-journey writeup (with all the dead-ends — HubSpot UI, Terraform SSH conflict, secure API change, Qdrant version drift) live at **[andreliar.github.io/QuartierScopeAI](https://andreliar.github.io/QuartierScopeAI/)**.

## License

MIT.
