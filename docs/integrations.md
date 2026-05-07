# Integrations

How each external system is wired in, with the gotchas we hit.

## data.gouv.fr MCP (officiel)

- **URL**: `https://mcp.data.gouv.fr/mcp`
- **Auth**: none (public endpoint, no rate limit advertised)
- **Maintained by**: data.gouv.fr team itself ([github.com/datagouv/datagouv-mcp](https://github.com/datagouv/datagouv-mcp))
- **Tools exposed**:
  - `search_datasets`, `get_dataset_info`, `list_dataset_resources`, `get_resource_info`
  - `query_resource_data` (Tabular API — only works on indexed resources)
  - `search_dataservices`, `get_dataservice_info`, `get_dataservice_openapi_spec` ← used for DVF discovery
  - `search_organizations`, `get_metrics`

### DVF — the Tabular API trap

We initially planned to query DVF directly via the Tabular API. **Spike result: 410 Gone.**

The DVF "Demandes de valeurs foncières géolocalisées" resource (UUID `d7933994-2c66-4131-a4da-cf7cd18040a4`) is published as a **499MB `.csv.gz`**, which the Tabular API does NOT index (it only works on uncompressed CSVs with consistent schema).

```bash
$ curl https://tabular-api.data.gouv.fr/api/resources/d7933994-2c66-4131-a4da-cf7cd18040a4/
HTTP 410 Gone
```

### DVF — the chosen path

1. Tools agent calls MCP `search_dataservices(q="DVF")` → finds the **API Données Foncières** (Cerema)
2. MCP `get_dataservice_openapi_spec(...)` → returns the OpenAPI YAML
3. Tools agent calls Cerema's REST API directly (still discovered via MCP, so the "MCP mandatory" deliverable holds)
4. Fallback: download `.csv.gz` once at boot, query locally with **DuckDB** (`SELECT … FROM read_csv_auto('dvf.csv.gz')`)

This actually demonstrates a *more advanced* capability than raw Tabular queries — **dynamic API discovery**.

## HubSpot Free + Service Keys (beta)

> ⚠️ HubSpot is mid-2025.2 platform migration. **"Private Apps" is being deprecated** in favour of **"Service Keys (beta)"**. Existing Private App tokens still work, but new tokens should be created as Service Keys. Both produce a `pat-na1-…` Bearer token usable identically against the CRM v3 API.

### How to create a Service Key (verified working path)

1. Login to your **regular HubSpot Hub** at [app.hubspot.com](https://app.hubspot.com) (not the Developer Portal — see the rabbit hole below for why)
2. Click the **⚙️ gear icon** (top-right) → **Settings**
3. Left sidebar → **Integrations** → **Service Keys (beta)**
4. **Create a new service key** — name it `QuartierScope AI`
5. Scopes (the 7 listed below)
6. Click **Generate** → use the **"Copy"** button (don't manually select — HubSpot truncates the displayed value with `…`)
7. Paste into droplet `.env` as `HUBSPOT_TOKEN=pat-na1-…`
8. `docker compose up -d --force-recreate app streamlit`

### API surface used

- **API base**: `https://api.hubapi.com/crm/v3/`
- **Auth**: `Authorization: Bearer pat-na1-…`
- **Scopes used**:
  ```
  crm.objects.contacts.read
  crm.objects.contacts.write
  crm.objects.deals.read
  crm.objects.deals.write
  crm.schemas.deals.read
  crm.schemas.deals.write
  crm.objects.owners.read
  ```
- **Tools (read)**: `get_contact`, `get_deal`
- **Tools (write, behind confirmation gate)**: `create_note`, `update_property` (4 custom `qs_*` fields), `create_task`

### HubSpot Free constraints (non-negotiable)

| Limit | Behaviour |
|---|---|
| 1 deal pipeline | Use existing — never auto-create |
| 1,000 contacts | Never auto-create — only attach |
| 2 users | AI is NOT a CRM user; writes via API on token holder's behalf |
| 100 custom properties / object | We use 4 on `deal`: `qs_neighborhood_score`, `qs_risk_level`, `qs_rental_yield_estimate`, `qs_last_analysis_at` |
| Email send 2k/mo | Disabled by default |

### HubSpot UI — the rabbit hole we fell into

HubSpot is mid-2025.2 platform migration. Under the hood, "Private Apps" is being replaced by "Service Keys" (still in beta as of writing). The path to a usable token is:

| Path | What you get |
|---|---|
| `app.hubspot.com/personal-access-key/<id>` | **CMS CLI key** — wrong product (themes & Source Code API) |
| `app.hubspot.com/private-apps/<id>` | "Your private apps have moved" → Legacy Apps in Developer Portal |
| Developer Portal → Legacy Apps → **Create legacy app** | **Public marketplace OAuth app** — wrong product |
| **Settings → Integrations → Service Keys (beta) → Create** ✅ | **CRM Service Key** with `pat-na1-…` token — what we want |

Lesson: when HubSpot's UI is in flux, search inside the Settings page rather than guessing URLs. See the [journey](/journey) page for the full saga.

## OpenAI

- API key only — no MCP for OpenAI
- Models: `gpt-4o-mini` (router) + `gpt-4o` (synthesis)
- Embeddings: `text-embedding-3-small` (1536-d)
- Cost projection: ~$10–20 over the 44h project

## Tavily

- API key from [app.tavily.com](https://app.tavily.com) (signup with GitHub, no credit card)
- Format: `tvly-…`
- Free tier 1,000 queries/month — plenty
- Used for qualitative quartier context (transports, sécurité, écoles)

## Langfuse v2 (self-hosted)

- Single Postgres + Next.js v2 process — no ClickHouse needed
- First-time visit at `http://<droplet-ip>/langfuse` asks to create an admin account
- Then create a project → grab `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` → set in droplet `.env`
- LangChain has a callback that auto-traces every chain invocation
