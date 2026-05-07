"""QS-200 — verifies conversation history is actually injected into agent prompts.

The PRD §9 + rubric §3 require: "Peux-tu approfondir ce point ?" must work,
i.e. the second turn must have access to the first turn's context.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.agents import router, synthesizer


@pytest.mark.asyncio
async def test_router_includes_history_in_prompt() -> None:
    """The router LLM call must receive the prior turns in its user message."""
    from app import config

    if not config.settings.openai_api_key:
        config.settings.openai_api_key = "sk-fake"

    history = [
        {"role": "user", "content": "Lyon 7e Guillotière, T2 LMNP 220k ?"},
        {"role": "assistant", "content": "Le LMNP est avantageux..."},
    ]

    captured: dict = {}

    class FakeLLM:
        async def ainvoke(self, messages, config=None):  # type: ignore[no-untyped-def]
            captured["messages"] = messages
            from langchain_core.messages import AIMessage

            return AIMessage(content='{"mode": "rag", "needs_action": false, "rationale": "ok"}')

    with patch.object(router, "ChatOpenAI", return_value=FakeLLM()):
        await router.classify("Approfondis ce point", deal_id=None, history=history)

    user_msg = next(m for m in captured["messages"] if m[0] == "user")
    assert "HISTORIQUE" in user_msg[1]
    assert "Lyon 7e Guillotière" in user_msg[1]


@pytest.mark.asyncio
async def test_synthesizer_includes_history_in_prompt() -> None:
    """The synthesizer LLM call must receive the prior turns."""
    from app import config

    if not config.settings.openai_api_key:
        config.settings.openai_api_key = "sk-fake"

    history = [
        {"role": "user", "content": "Comment évaluer un quartier ?"},
        {"role": "assistant", "content": "On regarde DVF, INSEE..."},
    ]
    rag = {"chunks": [{"source": "Wikipédia FR — DPE", "url": "x", "text": "DPE info", "score": 0.6}]}
    tools: dict = {"data": {}, "sources": []}

    captured: dict = {}

    class FakeLLM:
        async def ainvoke(self, messages, config=None):  # type: ignore[no-untyped-def]
            captured["messages"] = messages
            from langchain_core.messages import AIMessage

            return AIMessage(content="Réponse [Source: Wikipédia FR — DPE].")

    with patch.object(synthesizer, "ChatOpenAI", return_value=FakeLLM()):
        await synthesizer.synthesize("Refais pour une famille", rag, tools, history=history)

    user_msg = next(m for m in captured["messages"] if m[0] == "user")
    assert "HISTORIQUE" in user_msg[1]
    assert "Comment évaluer un quartier" in user_msg[1]


@pytest.mark.asyncio
async def test_history_truncated_to_last_6_messages() -> None:
    """No matter how long the history is, only the last 6 entries are kept."""
    long_history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"} for i in range(20)]
    formatted = router._format_history(long_history)
    assert "turn 19" in formatted
    assert "turn 0" not in formatted
    assert formatted.count("USER:") + formatted.count("ASSISTANT:") == 6


def test_empty_history_produces_empty_block() -> None:
    assert router._format_history([]) == ""
    assert router._format_history(None) == ""
    assert synthesizer._format_history_block([]) == ""
    assert synthesizer._format_history_block(None) == ""
