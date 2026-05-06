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


if __name__ == "__main__":
    app()
