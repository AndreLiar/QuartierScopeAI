---
layout: home

hero:
  name: QuartierScope AI
  text: Le coéquipier IA des cabinets CGP indépendants
  tagline: 2h d'étude de quartier → brief sourcé en 30 secondes, attaché au deal HubSpot. Données ouvertes en temps réel via le MCP officiel de data.gouv.fr.
  actions:
    - theme: brand
      text: Pitch en 2 phrases
      link: /overview#pitch
    - theme: alt
      text: Architecture
      link: /architecture
    - theme: alt
      text: Setup journey & lessons
      link: /journey

features:
  - icon: 🧠
    title: Multi-agents (LangGraph)
    details: Routeur + RAG (corpus expert) + Tools (DVF, INSEE, web) + Actions (HubSpot avec confirmation). 4 agents qui coopèrent au lieu d'un LLM seul.
  - icon: 🇫🇷
    title: data.gouv MCP officiel
    details: Connexion native au serveur MCP de data.gouv.fr (mcp.data.gouv.fr/mcp). DVF découvert dynamiquement via l'API Données Foncières du Cerema.
  - icon: 📋
    title: Citations exploitables AMF
    details: Chaque chiffre cliquable vers sa source. Lettre de Mission auditable directement à partir du brief.
  - icon: 🪝
    title: HubSpot Free natif
    details: Lecture + écriture (notes, propriétés custom, tâches) sans forcer l'équipe à upgrader. Toujours derrière une confirmation `[y/N]`.
  - icon: 🐳
    title: Déploiement single-host
    details: Docker Compose sur DigitalOcean droplet 4GB Premium AMS3. CI/CD GitHub Actions auto-deploy à chaque push.
  - icon: 🔒
    title: Sécurité by-default
    details: Pydantic input validation, secure headers, slowapi rate-limit, SSRF guards, prompt-injection mitigations, two-agent split pour les writes.
---

## En une phrase

> QuartierScope AI permet à un cabinet **CGP indépendant de 2 personnes** de **doubler son volume de dossiers d'investissement locatif** — en réduisant **2 heures d'étude de quartier à un brief sourcé de 30 secondes**, attaché automatiquement au bon deal HubSpot.

## État actuel

**v1 livré** (Sprints 1–4, ~44h) — multi-agents LangGraph en production pendant les sprints, puis **droplet décommissionné le 2026-05-10** pour stopper le run $24/mo. La stack reproduit à l'identique en local via `docker compose up -d`. Redeploy documenté dans [REDEPLOY.md](https://github.com/AndreLiar/QuartierScopeAI/blob/main/REDEPLOY.md) (~5 min).

- ✅ Infrastructure provisionnée puis décommissionnée (Terraform, DigitalOcean AMS3, $24/mo)
- ✅ Stack docker-compose (Caddy + FastAPI + Qdrant 264 chunks + Redis + Langfuse v2 + Postgres) — tourne en local
- ✅ CI/CD opérationnel (GitHub Actions, 3 workflows : CI, Deploy, Docs)
- ✅ Tous les secrets externes câblés (OpenAI, Tavily, HubSpot, MCP data.gouv)
- ✅ 4 agents coopératifs (Routeur + RAG + Tools + Actions) avec citations enforced
- ✅ Mémoire conversationnelle injectée dans les prompts (QS-200)
- ⏳ v1.5 (Sprints 5–8, ~50h) — simulateurs fiscaux Pinel/LMNP, PDF Lettre de Mission, scoring quantitatif
- ⏳ v2 (Sprint 9, ~8h) — multi-tenant

[→ Voir le détail des sprints](/sprints)
[→ Voir le journey complet (avec les ratés)](/journey)
