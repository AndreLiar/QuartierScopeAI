"""data.gouv.fr MCP client (QS-020).

Connects to the official streamable-HTTP MCP at https://mcp.data.gouv.fr/mcp.
"""

from __future__ import annotations

from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.config import settings


class DataGouvMCP:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or settings.mcp_datagouv_url
        self._cm = None
        self._session: ClientSession | None = None

    async def __aenter__(self) -> DataGouvMCP:
        self._cm = streamablehttp_client(self.url)
        read, write, _ = await self._cm.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session is not None:
            await self._session.__aexit__(*args)
        if self._cm is not None:
            await self._cm.__aexit__(*args)

    async def list_tools(self) -> list[dict[str, str | None]]:
        assert self._session is not None
        result = await self._session.list_tools()
        return [{"name": t.name, "description": t.description} for t in result.tools]

    async def call(self, tool: str, **arguments: Any) -> Any:
        assert self._session is not None
        result = await self._session.call_tool(tool, arguments=arguments)
        return result.content
