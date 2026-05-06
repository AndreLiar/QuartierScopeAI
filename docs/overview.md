# Overview & ICP

## Pitch {#pitch}

> **QuartierScope AI, c'est le coéquipier IA qui permet à un cabinet CGP indépendant de 2 personnes de doubler son volume de dossiers d'investissement locatif — en réduisant 2 heures d'étude de quartier à un brief sourcé de 30 secondes, attaché automatiquement au bon deal HubSpot.**
>
> **Connecté au serveur MCP officiel de data.gouv.fr (DVF, INSEE, zones à risque) avec des citations exploitables en Lettre de Mission AMF, il fonctionne nativement dans HubSpot Free — sans forcer l'équipe à upgrader son CRM.**

## Le problème

Pour un cabinet CGP indépendant qui conseille en investissement locatif (Pinel, LMNP, Denormandie), produire la note de quartier qui accompagne chaque recommandation prend **environ 2 heures par dossier**. Sur ~12 dossiers actifs en parallèle, c'est ~24h/semaine de recherche — soit **60% du temps utile** de chaque associé.

La douleur est aiguë parce que :

- La **Lettre de Mission AMF** doit citer des sources vérifiables pour chaque recommandation locative — pas de citations = risque de sanction AMF/ORIAS
- Embaucher un junior coûte 35k€ + charges + 6 mois de formation, et le marché locatif change trop vite
- Les outils existants (MeilleursAgents Pro, Castorus, Pricehubble) coûtent +200–400€/mois, n'ont pas de citations exploitables AMF, et ne se connectent pas à HubSpot

## La solution

Un copilote IA multi-agents qui :

1. **Comprend la requête** (routeur LangGraph) — méthodologie ? données live ? mixte ?
2. **Récupère l'expertise** (agent RAG) — corpus de 11 sources françaises (ANIL, Notaires de France, Cerema, INSEE, OLAP, ADEME, Banque de France, Service-public, MTE, AMF, ORIAS)
3. **Récupère les données live** (agent Tools) — DVF via Cerema (découvert via MCP), INSEE démographie, web search Tavily
4. **Synthétise** — un brief structuré avec citations cliquables
5. **Écrit dans HubSpot** (agent Actions) — note + propriétés custom sur le deal, **après confirmation `[y/N]`**

## L'ICP

**Cabinets CGP indépendants 2-5 personnes spécialisés en investissement locatif**, équipés de HubSpot Free.

| Critère | Petit cabinet CGP indé | Courtier crédit indé | Grand CGP / family office |
|---|---|---|---|
| Étude quartier = job | **Cœur du métier** | Optionnel (15 min HCSF) | Cœur mais déjà outillé |
| Décision d'achat | Co-fondateur, 1 semaine | Co-fondateur, 1 semaine | Comité, 6–18 mois |
| Stack CRM | HubSpot Free / Excel | HubSpot Free / Symphonie | Quantalys, O2S, Harvest |
| Régulation | ORIAS-CIF + AMF | ACPR-IOBSP | Idem |
| Goulot | **Bande passante humaine** | Vitesse banque | Coût marginal |
| Levier IA | **×2 capacité dossiers** | Marginal | Marginal |

**ICP retenu :** petit cabinet CGP indé. **Pas** les courtiers crédit (l'étude de quartier n'est pas leur cœur de métier — pivoté après recherche utilisateur).

### Persona — "Sarah & Marc, 2 associés à Lyon"

- SARL CGP, ORIAS (CIF + IOBSP + IAS), HubSpot Free
- Spécialité : conseil en investissement locatif, ticket moyen €200k–500k
- Volume actuel : ~12 dossiers actifs
- Volume cible avec QuartierScope : 20–25 (×2) sans embaucher

### Anti-ICP

- Investisseurs particuliers (B2C, pas de hook compliance)
- Courtiers crédit (étude de quartier = 15min, pas 2h)
- Grands réseaux CGP (cycle de vente trop long)
- Mandataires immobiliers (font de la prospection, pas de l'analyse de fond)

## Pourquoi GPT seul ne suffit pas

Un LLM seul :

- ❌ Ne peut pas accéder aux données ouvertes en temps réel (DVF, INSEE)
- ❌ Ne peut pas citer des sources vérifiables (hallucination → risque AMF)
- ❌ Ne peut pas écrire dans le CRM
- ❌ Ne peut pas appliquer une méthodologie experte interne (scoring quartier, risque locatif)

D'où l'architecture multi-agents : **le RAG + les Tools comblent les 4 limitations exactement.**

## Référence

Pour la spec produit complète, voir [`prd.md`](https://github.com/AndreLiar/QuartierScopeAI/blob/main/prd.md) dans le repo.
