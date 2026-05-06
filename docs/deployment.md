# Deployment & CI/CD

How code lands on the droplet automatically.

## Topology

```
DigitalOcean droplet — quartierscope-prod (AMS3, Basic 4GB, $24/mo)
├── Ubuntu 24.04 + Docker + Caddy
└── docker compose up:
    ├── caddy            (reverse proxy, port 80)
    ├── app              (FastAPI :8000 + Streamlit :8501)
    ├── qdrant           (vector DB :6333)
    ├── redis            (cache + state :6379)
    ├── langfuse-server  (trace UI :3000)
    └── langfuse-db      (Postgres :5432)
```

Public access: `http://165.22.192.94/` (no domain → no TLS for now).

## CI/CD pipeline

```
git push origin main
   │
   ├─→ CI workflow (.github/workflows/ci.yml)
   │   ├─ ruff check
   │   ├─ mypy (advisory)
   │   └─ pytest (incl. live MCP smoke test)
   │
   └─→ Deploy workflow (.github/workflows/deploy.yml)
       ├─ Setup SSH agent (private key from GitHub secret)
       ├─ Trust droplet host key
       ├─ rsync repo → quartierscope@165.22.192.94:~/quartierscope/
       ├─ Bootstrap .env on first deploy (generates Langfuse secrets)
       ├─ docker compose up -d --build
       └─ Health check: curl http://165.22.192.94/health (3-min poll)
```

**Every push to main auto-deploys to production.** PRs run CI only.

## GitHub Actions secrets

| Secret | Value | Set via |
|---|---|---|
| `SSH_PRIVATE_KEY` | Contents of `~/.ssh/do_ed25519` | `gh secret set` |
| `DROPLET_HOST` | `165.22.192.94` | `gh secret set` |

Set with:
```bash
cat ~/.ssh/do_ed25519 | gh secret set SSH_PRIVATE_KEY --repo AndreLiar/QuartierScopeAI
echo '165.22.192.94' | gh secret set DROPLET_HOST --repo AndreLiar/QuartierScopeAI
```

## Provisioning a fresh droplet (Terraform)

```bash
cd terraform/
export TF_VAR_do_token='dop_v1_...'
terraform init
terraform plan
terraform apply -auto-approve
```

Outputs:
- `droplet_ip`
- `ssh_command`
- `monthly_cost_usd`

The droplet is bootstrapped via cloud-init (`terraform/bootstrap.sh`):
- Installs Docker + Compose plugin
- Configures `ufw` (allows 22, 80, 443)
- Enables `fail2ban`
- Creates non-root `quartierscope` user with `docker` group access

## Local development

```bash
git clone https://github.com/AndreLiar/QuartierScopeAI
cd QuartierScopeAI
cp .env.example .env  # edit with your keys
docker compose up
```

Or for non-Docker dev:
```bash
uv pip install -e ".[dev]"
python -m app smoke      # validates data.gouv MCP connection
python -m app query "Bon quartier pour T2 LMNP à Lyon 7e ?"
uvicorn app.api:app --reload
```

## Health endpoints

| URL | Purpose |
|---|---|
| `http://<ip>/health` | API liveness (returns `{status: ok, version: 0.1.0}`) |
| `http://<ip>/docs` | OpenAPI auto-doc |
| `http://<ip>/api/query` | Multi-agent query endpoint |
| `http://<ip>/langfuse` | Langfuse trace UI |
| `http://<ip>/` | Streamlit demo (when QS-062 lands) |

## Memory & disk budgets

See [`architecture.md`](/architecture#memory-budget-on-the-4gb-droplet) for the full breakdown. TL;DR: ~2.5GB used of 4GB, ~15GB used of 80GB. Plenty of headroom.

## Rollback

`gh workflow run Deploy --ref <previous-good-sha>` re-runs the deploy workflow against an older commit. Or SSH in and `git reset --hard <sha> && docker compose up -d --build`.
