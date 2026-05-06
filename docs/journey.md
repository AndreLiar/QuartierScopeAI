# Setup journey & lessons learned

Chronological log of everything we did to get from an empty directory to a green CI/CD pipeline. Includes every detour and dead-end — they're the most useful part.

## Phase 0 — Empty repo, just a PRD

We started with a single file: `prd.md`. Architecture was defined on paper but no code, no infra, no tests. Decision : never start coding without first running a **feasibility spike** on the two riskiest assumptions.

### Spike 1 — Does the data.gouv MCP actually exist?

**Verdict: ✅ green.** The MCP is real, official, hosted publicly:

- URL: `https://mcp.data.gouv.fr/mcp`
- No auth, no rate-limit advertised
- 5 generic tools (`search_datasets`, etc.) — no DVF-specific tool, but DVF is queryable via the generic ones
- Maintained by the data.gouv.fr team itself ([github.com/datagouv/datagouv-mcp](https://github.com/datagouv/datagouv-mcp))

### Spike 2 — Is DVF queryable through the Tabular API?

**Verdict: ❌ failed (410 Gone).**

```bash
$ curl https://tabular-api.data.gouv.fr/api/resources/d7933994-2c66-4131-a4da-cf7cd18040a4/
HTTP 410 Gone
```

The DVF resource is published as a 499MB `.csv.gz`. The Tabular API only indexes uncompressed CSVs.

**Pivot**: route through MCP `search_dataservices` → discover the **API Données Foncières** (Cerema) → call that REST API directly. Same MCP-mandatory deliverable, more advanced demo (dynamic API discovery).

**Fallback**: download the `.csv.gz` once at boot, query locally with **DuckDB**.

### Why this saved time

Without these spikes, we would have committed to a Tabular-API-based architecture, hit the 410 mid-Sprint 2, and either delayed by 4-6h or shipped a broken demo. Two hours of feasibility work prevented a costly mid-flight pivot.

## Phase 1 — ICP pivot

Initial PRD targeted **mortgage brokers** (courtiers en crédit immobilier) for ACPR compliance reasons.

After forum research:

- ACPR audit-trail pain is real — but it's a 15-min HCSF check for credit brokers, not a 2h task
- The "2h neighborhood analysis" pain belongs to **CGP** (Conseillers en Gestion de Patrimoine) advising rental investments
- HubSpot in France markets explicitly to insurance brokers, not credit
- Forum complaints from brokers are about *bank response times*, not location due-diligence

**Pivot: target small CGP firms (2-5 people) on HubSpot Free.** Compliance hook becomes **AMF Lettre de Mission** (similar audit pressure, different acronym). Architecture stays identical — only the personas, demo script, and corpus emphasis shift.

**Lesson**: validate the persona's actual pain *before* committing to the architecture. The architecture survived; the marketing didn't.

## Phase 2 — Documenting everything before code

Before writing a single line of Python, we produced 3 living docs:

| Doc | Purpose | Length |
|---|---|---|
| [`prd.md`](https://github.com/AndreLiar/QuartierScopeAI/blob/main/prd.md) | What & why — scope, ICP, persona | 18 sections |
| [`ARCHITECTURE.md`](https://github.com/AndreLiar/QuartierScopeAI/blob/main/ARCHITECTURE.md) | How — C4 diagrams, sequences, deployment, decision log | 11 sections |
| [`SPRINTS.md`](https://github.com/AndreLiar/QuartierScopeAI/blob/main/SPRINTS.md) | Work breakdown — 10 epics, 22 stories, 4 sprints | DoR + DoD + risks |

Plus `CLAUDE.md` for future Claude instances to onboard quickly.

**Lesson**: docs as scaffolding. Once written, every subsequent decision had a place to land.

## Phase 3 — Provisioning the droplet (Terraform)

### Stumble 1 — SSH key already on DO

First `terraform apply`:

```
Error: SSH Key is already in use on your account
```

I had pre-existing keys on the DO account. Fix: switch from `resource "digitalocean_ssh_key"` to `data "digitalocean_ssh_key"` (lookup an existing key by name).

```hcl
# Before:
resource "digitalocean_ssh_key" "main" {
  public_key = file("~/.ssh/do_ed25519.pub")  # 422 conflict
}

# After:
data "digitalocean_ssh_key" "main" {
  name = "Andre-MBA-ed25519"
}
```

**Lesson**: when bootstrapping an account that already has state, prefer **data sources** over **resources**. Resources assume you own creation; data sources just look up.

### Success — droplet up in 43s

After the fix:
```
digitalocean_droplet.app: Creation complete after 43s
droplet_ip = "165.22.192.94"
monthly_cost_usd = "~$24/mo (Basic 4GB, ams3)"
```

cloud-init bootstrap took ~3 min more (Docker install). End state:
- Docker 29.4.2
- Compose v5.1.3
- ufw active (22/80/443)
- fail2ban active
- non-root `quartierscope` user with docker group

## Phase 4 — Scaffolding (in one shot)

Wrote 30+ files in a single batch session:
- `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `Caddyfile`, `.env.example`, `.dockerignore`
- `app/` — FastAPI thin, Typer CLI, Pydantic config, security middleware, agent stubs, MCP client
- `tests/test_smoke_mcp.py` — the QS-020 acceptance test
- `terraform/` — Droplet provisioning
- `.github/workflows/ci.yml` + `deploy.yml`

**Lesson**: scaffolding everything at once is faster than incremental — but only after the architecture is locked. Locked architecture → confident batched writes.

## Phase 5 — CI/CD setup

### First push, two failures

| Workflow | Failure | Cause |
|---|---|---|
| CI | `ruff` exit code 1 | Unused import in `app/memory/checkpointer.py` |
| Deploy | health check 500 errors | `secure` package API changed: `.framework.fastapi(response)` → `.set_headers(response)` |

Both fixes were one-liners. Pushed and the second deploy went green in **49s** (vs. 7m for the first one — Docker layer cache hit on the droplet).

**Lesson**: pin dependency major versions (`secure>=1,<2`) is necessary but not sufficient — the breaking change happened *within* a major. Always test container builds locally before pushing infra-dependent code.

## Phase 6 — Wiring secrets

### OpenAI ✅ — set on droplet via SSH

```bash
ssh quartierscope@165.22.192.94 "sed -i 's|^OPENAI_API_KEY=.*|OPENAI_API_KEY=sk-…|' ~/quartierscope/.env"
docker compose restart app
```

### Tavily ✅ — 2 minutes from app.tavily.com signup

### HubSpot — the saga

This took longer than provisioning the entire droplet. Sequence of dead-ends:

#### Dead-end 1 — `/personal-access-key/<id>`

User went to `https://app.hubspot.com/personal-access-key/48849852` and copied a token. Format `CiRuYTEt...` (base64).

That token is for the **HubSpot CMS CLI** — used to deploy themes/templates. **Not** a CRM API token. Scopes were all `developer.*`, `cms.*`, `developer.test_accounts.*`.

Real CRM API call returned 401.

#### Dead-end 2 — `/private-apps/<id>`

Direct URL to the canonical Private Apps page. Got: *"Your private apps have moved. We've consolidated all private apps into the new Legacy Apps page."*

#### Dead-end 3 — Legacy Apps in Developer Portal

"Legacy Apps" turned out to be **public marketplace OAuth apps** — for distributing apps to OTHER Hubs, not for accessing your own CRM. Wrong product.

#### Dead-end 4 — `/settings/<id>/integrations/private-apps`

```
That page is nowhere to be found
Try the following troubleshooting steps:
This link might be out-of-date.
```

HubSpot deprecated the URL.

#### Pivot — Service Keys (beta)

Inside Settings → Integrations, the user noticed a new option: **"Service keys (beta)"**. This turns out to be HubSpot's **2025.2 platform replacement for Private Apps** — exactly what we needed.

- Created with the 7 scopes I'd been listing
- Token format: `pat-na1-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` (standard HubSpot bearer, 36-char UUID after the prefix)
- Test call:
  ```
  GET /crm/v3/objects/deals  → HTTP 200 {"results":[]}
  GET /crm/v3/objects/contacts → HTTP 200 {"results":[]}
  ```
  ✅ both endpoints respond, scopes correct.

#### Truncated-token sub-saga

First attempt at copying showed `pat-na1-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXX` (6 chars in the last block, should be 12). HubSpot truncates the displayed token with `…`. The "Copy" button gives the full value.

After re-copy with the Copy button, the full 36-char UUID landed and the API call succeeded ✅

**Lesson**: when a SaaS UI is mid-migration, **trust the search bar, not URL guessing**. HubSpot has a search field inside Settings; typing "service key" or "private app" surfaces whatever live UI element handles that concern.

**Lesson 2**: always test bearer tokens with a real API call right after copying. A 401 immediately tells you it's truncated/malformed/wrong-product, before you waste time integrating.

## Phase 7 — Operational state at end of Sprint 1

| | |
|---|---|
| Droplet | `quartierscope-prod` AMS3, $24/mo |
| Containers | 6/6 healthy |
| CI | ✅ green (~47s) |
| Deploy | ✅ green (~49s after cache hit) |
| OpenAI | ✅ key set |
| Tavily | ✅ key set |
| HubSpot | ✅ token set, scopes verified |
| data.gouv MCP | ✅ smoke test in CI |
| Repo | [github.com/AndreLiar/QuartierScopeAI](https://github.com/AndreLiar/QuartierScopeAI) (private) |

Total elapsed time on infra + integrations: **~4 hours** of compressed work — about 1/10 of the 44h budget.

## Aggregate lessons

1. **Spikes before code.** 2h of feasibility checks saved 6h+ of mid-flight pivot.
2. **Validate the persona, not the spec.** The PRD said "courtier crédit" — real users said "CGP". The pivot was 30 min of doc edits and saved a misaligned demo.
3. **Docs as scaffolding.** Three living docs (PRD / ARCHITECTURE / SPRINTS) made batch-scaffolding 30+ files possible without thrash.
4. **Use data sources for pre-existing state.** Terraform `data` > `resource` when something already exists.
5. **Test bearer tokens immediately.** A 401 tells you instantly if it's truncated or wrong product.
6. **SaaS UIs in migration: search > URL.** HubSpot's Settings search bar found "Service Keys (beta)" when 4 different deep links failed.
7. **Pin dependency majors AND validate at build time.** `secure>=1,<2` allowed a breaking API change inside the major version.
8. **Cache-aware deploys.** First deploy 7m, second 49s — Docker layer cache on the droplet.
9. **Defer non-blocking work decisively.** When HubSpot setup hit ~30 min of friction, switching to Sprint 2 (no HubSpot dependency) preserved momentum.
