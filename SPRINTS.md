# SPRINTS.md — QuartierScope AI

Agile plan covering the 44h roadmap defined in `prd.md` §17. Importable into Linear / Jira / GitHub Projects.

- **Methodology**: 4 short sprints (~10–12h each), each ending in a demo-able increment.
- **Story IDs**: `QS-NNN`. Use them in commit messages (`QS-021: add DVF Cerema discovery`) and PR titles.
- **Estimation**: hours, not story points (the project is too short for points to add value).

## Completion status

**v1 (Sprints 1–4) = ✅ closed.** All 22 stories shipped to production except QS-091 (the 3-min demo recording, manual step). QS-022 (DuckDB DVF fallback) was deferred during v1 — moved to Sprint 7 (QS-121) to close it as part of v1.5.

**v1.5 (Sprints 5–7) = ⏳ planned, ~32h.** Closes the 4 gaps identified by evaluating v1 against the real CGP-immobilier playbook: fiscal simulators chiffrés (Pinel/LMNP/Denormandie), financing simulator, profitability scoring wired, client-facing PDF Lettre de Mission, live DVF transactions.

**v2 (Sprints 8–9) = ⏳ planned, ~26h.** SaaS-ifies the platform: programmes neufs marketplace + multi-tenant onboarding for other independent CGPs.

Verified live operational state during v1 (cloud paused since 2026-05-10 — droplet decommissioned to halt the $24/mo run; redeploy via [REDEPLOY.md](./REDEPLOY.md), ~5 min):

| | URL during v1 | URL today (local) |
|---|---|---|
| Streamlit demo | http://165.22.192.94/ | http://localhost:8501/ |
| API + OpenAPI | http://165.22.192.94/health · /docs | http://localhost:8000/health · /docs |
| Langfuse trace UI | http://165.22.192.94:3000 (traces flowing) | http://localhost:3100/ (v1 trace history restorable from `backups/langfuse-*.sql.gz`) |
| HubSpot proof of write | https://app.hubspot.com/contacts/48849852/record/0-3/60053552445 | (unchanged — cloud-side) |
| Public docs | https://andreliar.github.io/QuartierScopeAI/ | (unchanged — GitHub Pages) |
| Repo | https://github.com/AndreLiar/QuartierScopeAI | (unchanged) |

Status legend used below: ✅ shipped & verified · ⚠️ deferred (non-blocking) · ⏳ user action · ❌ removed in favour of a better approach.

## Sprint cadence

| Sprint | Phase | Hours | Sprint goal (demo-able outcome) | Status |
|---|---|---|---|---|
| **S1 — Foundation** | v1 | ~12h | "Sarah tape une commande sur le droplet et reçoit des transactions DVF live de Lyon 7e via le MCP officiel." | ✅ closed |
| **S2 — RAG + Tools complete** | v1 | ~10h | "QuartierScope produit un brief sourcé qui combine corpus expert et données live." | ✅ closed |
| **S3 — Orchestration + Actions** | v1 | ~12h | "Le brief s'attache automatiquement au deal HubSpot après confirmation `[y/N]`." | ✅ closed |
| **S4 — Quality, Frontend, Demo** | v1 | ~10h | "Le démo tourne en ligne (`http://<ip>`), trace visible dans Langfuse, tests passent." | ✅ closed |
| **S5 — Fiscal & financial simulators** | v1.5 | ~14h | "Le brief contient une simulation chiffrée: réduction Pinel €/an, cashflow LMNP €/mois, mensualité, capacité d'emprunt HCSF." | ⏳ planned |
| **S6 — Client-facing PDF artefacts** | v1.5 | ~10h | "Sarah clique 'Générer Lettre de Mission' → PDF audit-ready attaché au deal." | ⏳ planned |
| **S7 — Live DVF + comparative pricing** | v1.5 | ~8h | "Le brief montre les vraies transactions DVF récentes (médiane, écart, échantillon)." | ⏳ planned |
| **S8 — Marketplace & B2B integrations** | v2 | ~12h | "Sarah uploade son catalogue de programmes neufs; matching auto avec disclosure commission." | ⏳ planned |
| **S9 — Multi-tenant SaaS** | v2 | ~14h | "D'autres CGPs indépendants peuvent s'inscrire — auth, billing, données isolées." | ⏳ planned |

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

## v1.5 Roadmap — Fill the CGP-immobilier playbook gaps (~32h, 3 sprints)

Honest evaluation of v1 against what real CGP-immobilier cabinets do (Pinel/LMNP/Denormandie advisory + financing + clé-en-main accompagnement) showed v1 covers ~30–40 % of the playbook. v1 is the **compliance + analysis** layer; the missing 60% is **simulators chiffrés + client artefacts + live data**. v1.5 closes these gaps.

| Sprint | Phase | Hours | Goal |
|---|---|---|---|
| **S5 — Fiscal & financial simulators** | 9 | ~14h | "Le brief inclut une simulation chiffrée: réduction Pinel €/an, cashflow LMNP €/mois, mensualité, capacité d'emprunt HCSF — tout calculé, pas seulement cité." |
| **S6 — Client-facing PDF artefacts** | 10 | ~10h | "Sarah clique 'Générer Lettre de Mission' → PDF audit-ready (ORIAS/AMF header, simulations, citations cliquables) attaché automatiquement au deal HubSpot." |
| **S7 — Live DVF + comparative pricing** | 11 | ~8h | "Le brief montre les vraies transactions DVF récentes du quartier (médiane, écart, échantillon)." |

### E11 — Fiscal & financial simulators (~14h)

> Convertir les règles fiscales du RAG en chiffres exploitables pour ce client.

| ID | Story | Estimate |
|---|---|---|
| QS-100 | **Pinel simulator** — zones A bis/A/B1/B2, durées 6/9/12 ans, taux réformés 2024 (9/12/14%), plafonds loyer + ressources locataire. Returns: réduction totale €, réduction annuelle €, plafond loyer €/m². | 3h |
| QS-101 | **LMNP cashflow simulator** — micro-BIC (abattement 50%) vs réel (amortissement immo + mobilier), CSG/CRDS, IS/IR, comparison avec location nue. Returns: cashflow mensuel €, impôt économisé/an €, TRI apparent. | 3h |
| QS-102 | **Denormandie simulator** — éligibilité commune (liste ANRU + actions cœur de ville), plancher travaux ≥25 % du coût total, similaire à Pinel pour la réduction. | 2h |
| QS-103 | **Financing simulator** — mensualité (formule annuités), TAEG (assurance incluse), capacité d'endettement HCSF 35 %, scénarios apport 10/20/30 %. | 2h |
| QS-104 | **HCSF stress test** — recalcul mensualité avec taux +1 pp / +2 pp, alerte si capacité dépassée. | 1h |
| QS-105 | **Wire `app/tools/scoring.py`** (déjà stubbé) — `neighborhood_score(metrics)` combine prix médian DVF, INSEE jeunes/cadres, PPRI flag, accessibilité transports → 0-100 + 5 sous-scores. Populates `qs_neighborhood_score` HubSpot custom property (currently NULL). | 2h |
| QS-106 | **Tools agent integration** — invoke simulators when query mentions Pinel / LMNP / Denormandie / "rentabilité" / "mensualité". Heuristic match + parameter extraction (price, durée, zone). | 1h |
| QS-107 | **Synthesis mandatory section "Simulation chiffrée"** — when fiscal/financial sim data present in Tools output, force a section with concrete €€€ numbers in the brief. | 0.5h |

### E12 — Client-facing artefacts (~10h)

> Le livrable final pour le client : PDF Lettre de Mission audit-ready.

| ID | Story | Estimate |
|---|---|---|
| QS-110 | **PDF generator** (`app/tools/pdf.py`) — `weasyprint`, header ORIAS+AMF+SARL boilerplate, sections (résumé / éléments / simulations / recommandation / sources), pied de page avec disclaimer CIF. | 3h |
| QS-111 | **HubSpot file upload + association** — `POST /files/v3/files` (Free-tier compatible), associate to deal via `/crm/v3/objects/deals/{id}/associations/files`. | 2h |
| QS-112 | **PDF assembly** — pulls synth answer + Tools simulations + RAG citations cliquables + signature placeholders (CGP, client). | 2h |
| QS-113 | **Download endpoint** `GET /api/dossier/{deal_id}.pdf` — FastAPI streams the PDF blob. | 1h |
| QS-114 | **Streamlit "Télécharger Lettre de Mission" button** — appears alongside "Save to HubSpot"; hits the download endpoint, browser downloads. | 1h |
| QS-115 | **Audit log of generated PDFs** — Postgres table `dossier_audit` (deal_id, generated_at, query_hash, citations_used, broker_user) — compliance trail for ACPR/AMF inspection. | 1h |

### E13 — Live DVF + comparative pricing (~8h)

> Sortir du "données récentes non disponibles" — donner les vraies transactions.

| ID | Story | Estimate |
|---|---|---|
| QS-120 | **Real Cerema API call** — parse OpenAPI spec via MCP `get_dataservice_openapi_spec`, build typed httpx client, handle pagination, types Pydantic pour transactions. | 3h |
| QS-121 | **DuckDB fallback** (the deferred QS-022) — download dvf.csv.gz at boot or on-demand; `SELECT … FROM read_csv_auto('dvf.csv.gz') WHERE code_insee = ?`. Cache to `data/dvf_cache/`. | 2h |
| QS-122 | **Median computation** — prix médian €/m² par IRIS sur 12 derniers mois; nb transactions; écart-type. | 1h |
| QS-123 | **Comparative pricing** — compare le prix client (220 k€ / 45 m² = 4 888 €/m²) au médian, flag écart > ±15 %. | 1h |
| QS-124 | **Synthesis mandatory section "Données de marché"** — when DVF data present, force the section with median €/m², count, écart au prix client. | 1h |

---

## v2 Roadmap — SaaS-ify the platform (~26h, 2 sprints)

Beyond v1.5, the natural evolution is to **open the platform to other independent CGP cabinets** as a B2B SaaS tier — exactly the "vision business" called out in the user research.

| Sprint | Phase | Hours | Goal |
|---|---|---|---|
| **S8 — Marketplace & B2B integrations** | 12 | ~12h | "Sarah uploade son catalogue de programmes neufs; QuartierScope matche automatiquement le besoin client à 1-3 programmes éligibles, avec disclosure de toute commission." |
| **S9 — Multi-tenant SaaS** | 13 | ~14h | "Sarah peut inviter d'autres CGPs indépendants à utiliser leur propre QuartierScope tenant — auth, billing, données isolées." |

### E14 — Marketplace & B2B integrations (~12h)

| ID | Story | Estimate |
|---|---|---|
| QS-130 | **Programmes neufs catalog ingestion** — CSV/JSON upload, schema (commune, prix, surfaces, dispositifs Pinel/LMNP éligibles, livraison). Stored in Qdrant as a separate collection or in Postgres. | 3h |
| QS-131 | **Matching engine** — client criteria (budget, ville, dispositif fiscal cible, surface) → ranked list of 3 programmes. Hybrid: SQL filter + vector similarity on description. | 3h |
| QS-132 | **Conflict-of-interest tagging** — chaque programme a un flag `has_commission` + montant. Surface au client via le PDF Lettre de Mission. | 1h |
| QS-133 | **Notaire connector** — placeholder MCP-style integration (Notaires API, Notaviz, etc.); read-only initially (vérifier le bien existe au cadastre). | 2h |
| QS-134 | **Gestion locative connector** — webhooks pour statut "loué/vacant" feedback dans HubSpot deal lifecycle. | 2h |
| QS-135 | **Disclosure surfacing** — Lettre de Mission PDF affiche explicitement "ce cabinet perçoit X € de commission sur ce programme" si applicable. | 1h |

### E15 — Multi-tenant SaaS (~14h)

| ID | Story | Estimate |
|---|---|---|
| QS-140 | **Auth** — Clerk (Vercel Marketplace) or HubSpot OAuth. Each session bound to a `tenant_id`. | 3h |
| QS-141 | **Per-tenant Qdrant collection** — `tenant_{id}_corpus` (custom internal docs) en plus du corpus public partagé. Retrieval queries both. | 3h |
| QS-142 | **Stripe billing** — tiers (Solo €49/mo, Cabinet €149/mo, Studio €399/mo), metered overage on tokens > seuil. | 3h |
| QS-143 | **Tenant onboarding flow** — signup → HubSpot OAuth connect → corpus customization (upload internal scoring guide) → first query free. | 2h |
| QS-144 | **Usage metering** — tokens consumed, queries run, PDF dossiers generated, exposed in admin dashboard + Stripe usage record. | 2h |
| QS-145 | **Per-tenant rate limits** — slowapi keyed by tenant_id, per-tier overrides. | 1h |

---

## Sprint plans (v1.5 + v2)

### Sprint 5 — Fiscal & financial simulators (~14h)

**Demo**: same Sarah query, but the brief now contains a *Simulation chiffrée* section: "Pinel zone B1 12 ans → réduction de 31 680 € (2 640 €/an) — LMNP régime réel → cashflow +187 €/mois — Mensualité crédit (taux 4 %, 25 ans, apport 20 %) → 928 €/mois — Stress test +1 pp HCSF: capacité OK, dépasse à +2 pp."

**Risks**: Pinel rules change every loi de finances (annual). Mitigation: hardcode 2024 rules in a single source-of-truth dict per dispositif; tag with `effective_year` so re-runs flag stale.

### Sprint 6 — Client-facing PDF artefacts (~10h)

**Demo**: Sarah clicks "Télécharger Lettre de Mission" → 2-page PDF downloads with cabinet header, client name, simulations, citations as footnotes, signature blocks. Same PDF auto-attached to the HubSpot deal.

**Risks**: HubSpot Free file upload limit (5 docs/account historically). Mitigation: rotate older PDFs (delete > 6 months) automatically.

### Sprint 7 — Live DVF + comparative pricing (~8h)

**Demo**: brief shows "Lyon 7e Guillotière — médiane DVF 2024-2026 : **5 200 €/m²** (n=147 transactions). Le bien à 4 888 €/m² est **6 % sous le médian** — alignement de marché OK."

**Risks**: Cerema rate-limits or API down. Mitigation: DuckDB fallback (QS-121) is the safety net.

### Sprint 8 — Marketplace & B2B integrations (~12h)

**Demo**: Sarah uploads `programmes_neufs.csv` (20 lignes, ses partenaires promoteurs); next query for a Lyon Pinel client surfaces 2 matching programmes, with explicit "Commission cabinet : 4 200 €" disclosure on each.

**Risks**: legal — surfacing commissions might trigger contractual issues with promoteurs. Mitigation: opt-in per-tenant, default off; CGP toggle.

### Sprint 9 — Multi-tenant SaaS (~14h)

**Demo**: signup at `quartierscope.app/signup` (need domain, BL-108) → OAuth HubSpot → first 5 queries free → Stripe paywall → working multi-tenant deployment. Sarah invites 3 confrères CGP indé via referral.

**Risks**: data isolation bugs (one tenant seeing another's corpus) = catastrophic. Mitigation: integration test that seeds 2 tenants, runs queries, asserts cross-tenant leak == 0.

---

## Total budget after v1 + v1.5 + v2

| Phase | Hours | Cumulative |
|---|---|---|
| v1 (S1–S4, shipped) | ~44h | 44h |
| v1.5 (S5–S7) | ~32h | 76h |
| v2 (S8–S9) | ~26h | 102h |

102h gets QuartierScope from "compliance/analysis layer" to "full CGP-immobilier SaaS competitor" with multi-tenant onboarding ready.

---

## Backlog (out of any planned sprint)

The items below are still future-future or have been moved into scheduled sprints:

- ~~BL-100: Multi-tenant deployment~~ → moved to Sprint 9 (QS-141, QS-145)
- ~~BL-101: HubSpot OAuth app~~ → moved to Sprint 9 (QS-140)
- BL-102: Mistral default for GDPR-strict CGP customers (env toggle exists; needs benchmark + comms)
- BL-103: Langfuse v3 upgrade (needs droplet bump to 8GB)
- BL-104: Event-driven RAG re-ingestion pipeline
- BL-105: Next.js + Vercel AI Chat SDK frontend (replaces Streamlit when SaaS scale demands it)
- BL-106: HubSpot 2-way sync (CRM updates pulled back into context for follow-up queries)
- BL-107: Mortgage-broker pivot v2 (different RAG corpus, ACPR audit hook)
- BL-108: Custom domain + Caddy auto-TLS (`quartierscope.app`) — prerequisite for Sprint 9
- ~~BL-109: DO Spaces for shared DVF cache~~ → addressed by Sprint 7 (QS-121 DuckDB local cache)
- BL-110: Migrate HubSpot integration to "MCP Auth Apps" (HubSpot's native MCP server) once it leaves beta
- BL-111: White-label tenant theming (logos, colors) — for Cabinet/Studio tiers
- BL-112: Mobile app (React Native) — Sarah on the road during client visits
- BL-113: Compliance auto-report — quarterly PDF aggregating all dossiers generated, for ACPR/AMF preparation

---

## How to use this in Linear / Jira / GitHub Projects

- **Linear**: each epic = a Project; each story = an Issue; map sprints to Cycles.
- **Jira**: each epic = an Epic; stories = User Stories under it; sprints = Scrum sprints.
- **GitHub Projects**: one Project board, columns = sprints, items linked to issues.
- **Commit / PR convention**: prefix with story ID — `QS-021: implement DVF Cerema discovery via MCP`. Makes the story → commit traceability automatic.
