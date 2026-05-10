import asyncio
import json
import os
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.tree import Tree

from app.orchestrator import run as orchestrator_run

app = typer.Typer(help="QuartierScope AI — analyse de quartier pour CGP indé.")
console = Console()

MAX_HISTORY_TURNS = 6


def _session_file() -> Path:
    """Pick the first writable parent directory in this preference order:
    /app/data (Docker volume) → $HOME → tempdir.
    """
    tmp = Path(tempfile.gettempdir())
    for parent in (Path("/app/data"), Path(os.environ.get("HOME") or tmp), tmp):
        try:
            target = parent / ".quartierscope_session.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch(exist_ok=True)
            return target
        except (PermissionError, OSError):
            continue
    return tmp / "quartierscope_session.json"


def _load_history() -> list[dict]:
    sf = _session_file()
    if not sf.exists() or sf.stat().st_size == 0:
        return []
    try:
        return json.loads(sf.read_text(encoding="utf-8"))[-MAX_HISTORY_TURNS:]
    except Exception:
        return []


def _save_history(history: list[dict]) -> None:
    sf = _session_file()
    try:
        sf.write_text(json.dumps(history[-MAX_HISTORY_TURNS:], ensure_ascii=False), encoding="utf-8")
    except (PermissionError, OSError):
        pass


@app.command()
def query(
    text: str = typer.Argument(..., help="La question à poser"),
    deal: str | None = typer.Option(None, help="ID du deal HubSpot pour rattacher l'analyse"),
    new_session: bool = typer.Option(False, "--new", help="Reset conversation history before answering"),
) -> None:
    if new_session:
        _save_history([])
    history = _load_history()
    if history:
        console.print(f"[dim]Historique: {len(history)} message(s) précédent(s) — utilise --new pour reset[/dim]")
    result = asyncio.run(orchestrator_run(query=text, history=history, deal_id=deal, confirm=False))
    history.append({"role": "user", "content": text})
    if not result.get("refused"):
        history.append({"role": "assistant", "content": result.get("answer", "")[:1000]})
    _save_history(history)

    tree = Tree(f"[bold]Question:[/bold] {text}")
    for step in result.get("trace", []):
        tree.add(f"[yellow]{step.get('step', '?')}[/yellow] → {step.get('detail', '...')}")
    console.print(tree)

    if result.get("refused"):
        console.print(f"\n[red]✗ refusé:[/red] {result.get('answer', '')}")
        return

    console.print(f"\n[bold]Réponse:[/bold]\n{result.get('answer', '')}\n")

    if result.get("citations"):
        console.print("[bold]Citations:[/bold]")
        for c in result["citations"]:
            console.print(f"  • [cyan]{c.get('source', '?')}[/cyan] ({c.get('score', 0):.2f})")
            console.print(f"    {c.get('url', '')}")

    if result.get("proposed_actions"):
        console.print("\n[bold yellow]Actions proposées:[/bold yellow]")
        for a in result["proposed_actions"]:
            console.print(f"  • {a.get('preview', a.get('tool'))}")
        if typer.confirm("Confirmer l'écriture HubSpot ?", default=False):
            confirmed_result = asyncio.run(
                orchestrator_run(query=text, history=[], deal_id=deal, confirm=True)
            )
            for r in confirmed_result.get("receipts", []):
                colour = "green" if r.get("status") == "ok" else "red"
                console.print(f"  [{colour}]→ {r.get('tool')}: {r.get('status')}[/{colour}]")


@app.command()
def smoke() -> None:
    from tests.test_smoke_mcp import main_async

    asyncio.run(main_async())


@app.command()
def dvf(
    commune: str = typer.Argument(..., help="Code INSEE (ex: 69387 pour Lyon 7e)"),
    year_from: int = typer.Option(2024, "--from"),
    year_to: int | None = typer.Option(None, "--to"),
) -> None:
    """QS-021 — discover Cerema API via data.gouv MCP, fetch DVF stats."""
    from app.tools.dvf import discover_cerema_api, query_transactions

    async def _run() -> None:
        console.print("[bold]Discovering Cerema DVF API via data.gouv MCP…[/bold]")
        discovery = await discover_cerema_api()
        console.print(f"[green]✓[/green] {discovery['name']}")
        if discovery.get("base_url"):
            console.print(f"  base_url: {discovery['base_url']}")
        else:
            console.print("  [yellow](base_url not provided by MCP — using default reference)[/yellow]")

        console.print(f"\n[bold]Querying transactions for {commune}…[/bold]")
        stats = await query_transactions(commune, year_from=year_from, year_to=year_to)
        console.print(stats)

    asyncio.run(_run())


@app.command()
def rag(query_text: str = typer.Argument(..., help="Question pour le RAG")) -> None:
    """QS-032 — retrieve from corpus with citation enforcement."""
    from app.agents.rag_agent import retrieve

    async def _run() -> None:
        result = await retrieve(query_text)
        if result["refused"]:
            console.print("[red]✗ aucun chunk pertinent — réponse refusée (politique citation, PRD §13.2)[/red]")
            return
        console.print(f"[green]✓[/green] {len(result['chunks'])} chunks, {len(result['citations'])} sources distinctes\n")
        for c in result["citations"]:
            console.print(f"[cyan]{c['source']}[/cyan]  (score={c['score']:.2f})")
            console.print(f"  {c['url']}")
            console.print(f"  {c['snippet'][:200]}…\n")

    asyncio.run(_run())


@app.command()
def ingest_corpus() -> None:
    """QS-030/031/033 — download + chunk + embed + upsert the 11-source corpus."""
    from app.ingest import main as ingest_main

    ingest_main()


@app.command()
def web(query_text: str = typer.Argument(..., help="Recherche web (Tavily)")) -> None:
    """QS-023 — Tavily web search with SSRF guard."""
    from app.tools.web_search import search

    async def _run() -> None:
        results = await search(query_text, max_results=5)
        if not results:
            console.print("[yellow]no results (TAVILY_API_KEY missing?)[/yellow]")
            return
        for r in results:
            console.print(f"\n[cyan]{r['title']}[/cyan]")
            console.print(f"  {r['url']}")
            console.print(f"  {r['content'][:200]}…")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
