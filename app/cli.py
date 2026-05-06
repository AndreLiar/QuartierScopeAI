import asyncio

import typer
from rich.console import Console
from rich.tree import Tree

from app.orchestrator import run as orchestrator_run

app = typer.Typer(help="QuartierScope AI — analyse de quartier pour CGP indé.")
console = Console()


@app.command()
def query(
    text: str = typer.Argument(..., help="La question à poser"),
    deal: str | None = typer.Option(None, help="ID du deal HubSpot pour rattacher l'analyse"),
) -> None:
    result = asyncio.run(orchestrator_run(query=text, history=[], deal_id=deal))

    tree = Tree(f"[bold]Question:[/bold] {text}")
    for step in result.get("trace", []):
        tree.add(f"[yellow]{step.get('step', '?')}[/yellow] → {step.get('detail', '...')}")
    tree.add(f"[green]Final[/green] → {result.get('answer', '')[:120]}")
    console.print(tree)

    if result.get("citations"):
        console.print("\n[bold]Citations:[/bold]")
        for c in result["citations"]:
            console.print(f"  - {c.get('source', '?')}: {c.get('url', '')}")

    if result.get("proposed_actions"):
        console.print("\n[bold red]Actions proposées:[/bold red]")
        for a in result["proposed_actions"]:
            console.print(f"  - {a}")
        confirm = typer.confirm("Confirmer l'écriture HubSpot ?", default=False)
        if confirm:
            console.print("[green]→ écriture (stub QS-052)[/green]")


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
        if discovery is None:
            console.print("[red]✗ no DVF dataservice found[/red]")
            return
        console.print(f"[green]✓[/green] found: [cyan]{discovery['name']}[/cyan]")
        console.print(f"  base_url: {discovery.get('base_url')}")

        console.print(f"\n[bold]Querying transactions for {commune}…[/bold]")
        stats = await query_transactions(commune, year_from=year_from, year_to=year_to)
        console.print(stats)

    asyncio.run(_run())


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
