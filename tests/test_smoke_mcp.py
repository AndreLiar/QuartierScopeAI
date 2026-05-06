"""QS-020 — end-to-end smoke test: data.gouv MCP server is reachable and returns DVF.

Run: `pytest tests/test_smoke_mcp.py -v` or `python -m app smoke`
"""

from __future__ import annotations

import asyncio

import pytest

from app.tools.datagouv_mcp import DataGouvMCP


@pytest.mark.asyncio
async def test_list_tools_includes_dataset_tools() -> None:
    async with DataGouvMCP() as client:
        tools = await client.list_tools()
        names = {t["name"] for t in tools}
        assert "search_datasets" in names, f"got: {names}"
        assert "search_dataservices" in names, f"got: {names}"


@pytest.mark.asyncio
async def test_search_dvf_dataset() -> None:
    async with DataGouvMCP() as client:
        result = await client.call("search_datasets", q="demandes de valeurs foncières")
        assert result is not None


async def main_async() -> None:
    """Standalone runner via `python -m app smoke`."""
    from rich.console import Console

    console = Console()

    console.print("[bold]Connecting to data.gouv MCP…[/bold]")
    async with DataGouvMCP() as client:
        tools = await client.list_tools()
        console.print(f"[green]✓[/green] connected — {len(tools)} tools available")
        for t in tools:
            console.print(f"  - [cyan]{t['name']}[/cyan]")

        console.print("\n[bold]Searching DVF datasets…[/bold]")
        result = await client.call("search_datasets", q="demandes de valeurs foncières")
        console.print(result)

        console.print("\n[bold]Discovering API Données Foncières via dataservices…[/bold]")
        result = await client.call("search_dataservices", q="DVF")
        console.print(result)


if __name__ == "__main__":
    asyncio.run(main_async())
