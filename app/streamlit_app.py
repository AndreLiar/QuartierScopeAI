"""QS-062 — Streamlit demo page.

Calls the local FastAPI /query endpoint, renders the multi-agent trace,
the answer with inline citations, and a Save-to-HubSpot button that
re-invokes with confirm=true.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

API_BASE = os.environ.get("STREAMLIT_API_BASE", "http://localhost:8000")
TIMEOUT = 90.0

st.set_page_config(
    page_title="QuartierScope AI",
    page_icon="🏘️",
    layout="wide",
)

st.markdown(
    """
    <h1 style="margin-bottom:0">QuartierScope AI</h1>
    <p style="color:#666;font-size:1.05rem">
      Le coéquipier IA des cabinets CGP indépendants — 2h de due-diligence
      quartier compressées en 30 secondes, attachées au bon deal HubSpot.
    </p>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Persona démo")
    st.caption("**Sarah & Marc** — co-fondateurs cabinet CGP 2 personnes à Lyon.")
    st.caption("Spécialité : conseil en investissement locatif (Pinel, LMNP, Denormandie).")
    st.divider()
    st.markdown("### État")
    try:
        h = httpx.get(f"{API_BASE}/health", timeout=3).json()
        st.success(f"API live · v{h.get('version', '?')}")
    except Exception:
        st.error("API injoignable")
    st.divider()
    st.markdown("### Liens")
    st.caption("[Repo](https://github.com/AndreLiar/QuartierScopeAI)")
    st.caption("[Docs](https://andreliar.github.io/QuartierScopeAI/)")
    st.caption("[Langfuse traces](/langfuse)")


col_q, col_d = st.columns([3, 1])
with col_q:
    query = st.text_input(
        "Question quartier",
        value="Lyon 7e Guillotière, T2 LMNP 220k pour primo-investisseur — quel score de risque et tension locative ?",
    )
with col_d:
    deal_id = st.text_input("Deal HubSpot (optionnel)", value="")

run_btn = st.button("Lancer l'analyse", type="primary")


def _post_query(query: str, deal_id: str | None, confirm: bool) -> dict[str, Any]:
    payload = {"query": query, "history": [], "confirm": confirm}
    if deal_id:
        payload["deal_id"] = deal_id
    r = httpx.post(f"{API_BASE}/query", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _render_trace(trace: list[dict]) -> None:
    if not trace:
        return
    with st.expander("🧭 Trace de routage (LangGraph)", expanded=True):
        for step in trace:
            st.markdown(f"**{step.get('step', '?')}** → {step.get('detail', '')}")


def _render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    st.markdown("### Sources citées")
    cols = st.columns(min(len(citations), 3) or 1)
    for i, c in enumerate(citations):
        with cols[i % len(cols)]:
            st.markdown(
                f"**{c.get('source', '?')}**  \n"
                f"<small style='color:#666'>score {c.get('score', 0):.2f}</small>  \n"
                f"[{c.get('url', '')}]({c.get('url', '')})  \n"
                f"<small>{(c.get('snippet') or '')[:180]}…</small>",
                unsafe_allow_html=True,
            )


def _render_actions_bar(result: dict) -> None:
    proposed = result.get("proposed_actions") or []
    if not proposed:
        return
    st.markdown("### Actions proposées sur HubSpot")
    for a in proposed:
        st.markdown(f"- {a.get('preview', a.get('tool'))}")
    if st.button("✅ Confirmer l'écriture HubSpot", type="primary"):
        with st.spinner("Écriture HubSpot…"):
            confirmed = _post_query(query, deal_id or None, confirm=True)
        receipts = confirmed.get("receipts") or []
        for r in receipts:
            tool = r.get("tool", "?")
            status = r.get("status", "?")
            if status == "ok":
                st.success(f"{tool} → ok ({r.get('id')})")
            else:
                st.error(f"{tool} → {r.get('error', 'error')}")


if run_btn and query:
    with st.spinner("Routeur → RAG → Tools → Synthèse…"):
        try:
            result = _post_query(query, deal_id or None, confirm=False)
        except httpx.HTTPError as exc:
            st.error(f"Erreur API: {exc}")
            st.stop()

    _render_trace(result.get("trace", []))

    if result.get("refused"):
        st.warning(result.get("answer") or "Réponse refusée (politique de citation).")
    else:
        st.markdown("### Réponse")
        st.write(result.get("answer", "—"))
        _render_citations(result.get("citations", []))
        _render_actions_bar(result)

st.divider()
st.caption("Multi-agents : Routeur (gpt-4o-mini) · RAG (Qdrant 264 chunks) · Tools (data.gouv MCP + Tavily) · Actions (HubSpot)")
