"""QS-040 — LangGraph state machine wiring all 4 agents.

Single entrypoint shared by CLI, FastAPI, and Streamlit:
    result = await orchestrator.run(query, history, deal_id, confirm=False)

Flow:
    START → route → rag → tools → synthesize → (propose_actions) → END

Each agent node is resilient: if the agent returns an empty/refused result,
the next node still runs. The synthesizer enforces the citation policy.
"""

from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents import actions_agent, rag_agent, router, synthesizer, tools_agent

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    query: str
    deal_id: str | None
    history: list[dict]
    decision: dict
    rag: dict
    tools: dict
    synthesis: dict
    proposed_actions: list[dict]
    confirm: bool
    receipts: list[dict]
    trace: list[dict]


class OrchestratorResult(TypedDict):
    answer: str
    trace: list[dict]
    citations: list[dict]
    proposed_actions: list[dict]
    receipts: list[dict]
    refused: bool


async def _route_node(state: GraphState) -> dict:
    decision = await router.classify(state["query"], state.get("deal_id"))
    return {
        "decision": decision,
        "trace": (state.get("trace") or [])
        + [
            {
                "step": "Routeur",
                "detail": f"mode={decision['mode']} action={decision['needs_action']} — {decision['rationale']}",
            }
        ],
    }


async def _rag_node(state: GraphState) -> dict:
    if state["decision"]["mode"] not in ("rag", "rag+tools"):
        return {"rag": {"chunks": [], "citations": [], "refused": False}}
    rag = await rag_agent.retrieve(state["query"])
    return {
        "rag": rag,
        "trace": (state.get("trace") or [])
        + [
            {
                "step": "RAG",
                "detail": f"{len(rag['chunks'])} chunks, {len(rag['citations'])} sources",
            }
        ],
    }


async def _tools_node(state: GraphState) -> dict:
    if state["decision"]["mode"] not in ("tools", "rag+tools"):
        return {"tools": {"data": {}, "sources": []}}
    tools = await tools_agent.run_tools(state["query"])
    return {
        "tools": tools,
        "trace": (state.get("trace") or [])
        + [
            {
                "step": "Tools",
                "detail": f"data keys={list(tools['data'].keys())} sources={len(tools['sources'])}",
            }
        ],
    }


async def _synth_node(state: GraphState) -> dict:
    synth = await synthesizer.synthesize(state["query"], state.get("rag", {}), state.get("tools", {}))
    return {
        "synthesis": synth,
        "trace": (state.get("trace") or [])
        + [
            {
                "step": "Synthèse",
                "detail": f"refused={synth['refused']} citations={len(synth.get('citations', []))}",
            }
        ],
    }


async def _propose_actions_node(state: GraphState) -> dict:
    plan = await actions_agent.propose(
        state["query"], state.get("synthesis", {}), state.get("deal_id")
    )
    next_trace = (state.get("trace") or []) + [
        {"step": "Actions", "detail": f"proposed={len(plan)}"}
    ]

    if state.get("confirm") and plan:
        receipts = await actions_agent.execute(plan)
        next_trace.append(
            {"step": "Actions/exec", "detail": f"{len(receipts)} writes"}
        )
        return {"proposed_actions": plan, "receipts": receipts, "trace": next_trace}

    return {"proposed_actions": plan, "receipts": [], "trace": next_trace}


def _route_after(state: GraphState) -> str:
    if state["decision"]["needs_action"] and state.get("deal_id"):
        return "propose_actions"
    return END


def _build_graph():  # type: ignore[no-untyped-def]
    builder = StateGraph(GraphState)
    builder.add_node("router_node", _route_node)
    builder.add_node("retrieve_rag", _rag_node)
    builder.add_node("run_tools", _tools_node)
    builder.add_node("synthesize", _synth_node)
    builder.add_node("propose_actions", _propose_actions_node)

    builder.add_edge(START, "router_node")
    builder.add_edge("router_node", "retrieve_rag")
    builder.add_edge("retrieve_rag", "run_tools")
    builder.add_edge("run_tools", "synthesize")
    builder.add_conditional_edges(
        "synthesize",
        _route_after,
        {"propose_actions": "propose_actions", END: END},
    )
    builder.add_edge("propose_actions", END)
    return builder.compile()


_GRAPH = None


def graph():  # type: ignore[no-untyped-def]
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


async def run(
    query: str,
    history: list[dict] | None = None,
    deal_id: str | None = None,
    confirm: bool = False,
) -> OrchestratorResult:
    initial: GraphState = {
        "query": query,
        "deal_id": deal_id,
        "history": history or [],
        "confirm": confirm,
        "trace": [],
    }
    final: GraphState = await graph().ainvoke(initial)  # type: ignore[arg-type,assignment]

    synth = final.get("synthesis", {})
    return {
        "answer": synth.get("answer", ""),
        "trace": final.get("trace", []),
        "citations": synth.get("citations", []),
        "proposed_actions": final.get("proposed_actions", []),
        "receipts": final.get("receipts", []),
        "refused": synth.get("refused", False),
    }
