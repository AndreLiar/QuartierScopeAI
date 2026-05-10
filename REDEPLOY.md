# Redeploy

How to bring QuartierScope back up on a fresh DigitalOcean droplet after a `terraform destroy`.

## Local Docker (always available)

The full stack runs locally on macOS / Linux without any cloud infra:

```bash
cp backups/.env-droplet .env             # or restore from your password manager
docker compose up -d                      # 6 services: app, streamlit, qdrant, redis, langfuse-db, langfuse-server
docker compose exec app python -m app ingest-corpus   # ~1-2 min, 12 sources, 264 chunks
```

Surfaces:
- FastAPI: http://localhost:8000/health · /docs
- Streamlit: http://localhost:8501/
- Langfuse: http://localhost:3100/ (remapped from 3000 to avoid host port conflicts)

Caddy is intentionally gated behind a `proxy` profile in `docker-compose.override.yml` — not needed on localhost (and hits a macOS Docker Desktop file-lock issue on the bind-mounted Caddyfile). To enable it: `docker compose --profile proxy up -d`.

`docker-compose.override.yml` is gitignored — it's per-developer config that adapts the production compose file for local dev (publish ports directly, skip Caddy, remap Langfuse).

## Restoring Langfuse trace history (optional)

After local stack is up, if you want to restore the v1 production traces from `backups/langfuse-*.sql.gz`:

```bash
gzip -dc backups/langfuse-YYYYMMDDTHHMMSSZ.sql.gz | docker compose exec -T langfuse-db psql -U postgres langfuse
```

## Cloud redeploy (DigitalOcean)

When ready to pay $24/mo again:

1. **Provision droplet:**
   ```bash
   cd terraform/
   TF_VAR_do_token=$DO_TOKEN terraform apply
   ```
   Note the new `droplet_ip` from the output — this will differ from the old `165.22.192.94`.

2. **Update GitHub Actions secret:**
   ```bash
   gh secret set DROPLET_HOST --body "<new-ip>" --repo AndreLiar/QuartierScopeAI
   ```

3. **Bootstrap droplet:** `terraform/bootstrap.sh` runs as user-data on first boot — installs Docker + clones the repo. Wait ~2 min for cloud-init to finish.

4. **Repopulate `.env` on droplet:**
   ```bash
   scp -i ~/.ssh/do_ed25519 backups/.env-droplet quartierscope@<new-ip>:~/quartierscope/.env
   ssh -i ~/.ssh/do_ed25519 quartierscope@<new-ip> "cd ~/quartierscope && \
     sed -i 's|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://localhost:8501,http://<new-ip>|' .env && \
     sed -i 's|DROPLET_HOST=.*|DROPLET_HOST=<new-ip>|' .env"
   ```

5. **Trigger deploy:** push to `main` (or re-run the latest Deploy workflow). The deploy workflow rsyncs the repo and runs `docker compose up -d --build --force-recreate`.

6. **Ingest corpus:**
   ```bash
   ssh -i ~/.ssh/do_ed25519 quartierscope@<new-ip> "cd ~/quartierscope && docker compose exec -T app python -m app ingest-corpus"
   ```

7. **Update docs/CLAUDE.md/README.md** — replace any remaining `165.22.192.94` references with the new IP.

## What survives a destroy

- HubSpot data (cloud, untouched)
- OpenAI / Tavily / HubSpot / Langfuse keys (in `backups/.env-droplet`)
- Langfuse trace history (in `backups/langfuse-*.sql.gz`)
- GitHub Actions `SSH_PRIVATE_KEY` secret

## What dies with a destroy

- Qdrant 264 chunks (rebuildable via `ingest-corpus`)
- Redis cache (ephemeral)
- The droplet's IP — a new one is assigned on `terraform apply`
- Anything written to the droplet outside `~/quartierscope/` (none by default)
