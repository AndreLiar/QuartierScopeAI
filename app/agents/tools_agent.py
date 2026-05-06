"""Tools agent — read-only data tools (DVF, INSEE, web). Wire in QS-021/022/023."""

from typing import TypedDict


class ToolsResult(TypedDict):
    data: dict
    sources: list[dict]


async def run_tools(query: str) -> ToolsResult:
    return {"data": {}, "sources": []}
