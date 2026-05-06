"""QS-042 — synthesizer post-filter unit tests.

Verifies that hallucinated source names are stripped before the answer
ever reaches HubSpot or the user.
"""

from __future__ import annotations

from app.agents.synthesizer import _build_citations_list, _filter_citations


def test_filter_citations_strips_hallucinated_source() -> None:
    answer = (
        "Le quartier est cher [Source: Buddey]. "
        "Le DPE est noté C [Source: Wikipédia FR — DPE]."
    )
    valid = {"Wikipédia FR — DPE", "Wikipédia FR — Loi Pinel"}
    cleaned, used = _filter_citations(answer, valid)
    assert "Buddey" not in cleaned
    assert "[Source: Wikipédia FR — DPE]" in cleaned
    assert used == ["Wikipédia FR — DPE"]


def test_filter_citations_resolves_partial_match() -> None:
    answer = "Loyer encadré [Source: Wikipédia FR — DPE]."
    valid = {"Wikipédia FR — Diagnostic de performance énergétique (DPE)"}
    cleaned, used = _filter_citations(answer, valid)
    assert "Diagnostic de performance énergétique" in cleaned
    assert used == ["Wikipédia FR — Diagnostic de performance énergétique (DPE)"]


def test_filter_citations_dedup() -> None:
    answer = "[Source: A] foo [Source: A] bar [Source: B]"
    _, used = _filter_citations(answer, {"A", "B"})
    assert used == ["A", "B"]


def test_build_citations_list_only_used_sources() -> None:
    chunks = [
        {"source": "A", "url": "u_a", "text": "txt_a", "score": 0.9},
        {"source": "B", "url": "u_b", "text": "txt_b", "score": 0.8},
        {"source": "C", "url": "u_c", "text": "txt_c", "score": 0.7},
    ]
    used = ["B", "A"]
    citations = _build_citations_list(used, chunks, [])
    assert [c["source"] for c in citations] == ["B", "A"]
    assert all("score" in c for c in citations)


def test_filter_citations_handles_no_matches() -> None:
    answer = "Tout vient de [Source: ChatGPT-Knows-This]."
    cleaned, used = _filter_citations(answer, {"Wikipédia FR — DPE"})
    assert "Source:" not in cleaned
    assert used == []
