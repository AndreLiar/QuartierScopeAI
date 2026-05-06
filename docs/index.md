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

Le projet est un **PoC 44h** documenté en mode "show your work":

- ✅ Infrastructure provisionnée (Terraform, DigitalOcean AMS3, $24/mo)
- ✅ Stack docker-compose (Caddy + FastAPI + Qdrant + Redis + Langfuse v2 + Postgres)
- ✅ CI/CD opérationnel (GitHub Actions auto-deploy sur push to main)
- ✅ Tous les secrets externes câblés (OpenAI, Tavily, HubSpot, MCP data.gouv)
- ⏳ Sprint 2 en cours — agents RAG + Tools

[→ Voir le détail des sprints](/sprints)
[→ Voir le journey complet (avec les ratés)](/journey)
