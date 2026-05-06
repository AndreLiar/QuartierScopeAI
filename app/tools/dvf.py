"""DVF tool — Cerema API (discovered via MCP) with DuckDB fallback. Wire in QS-021/022."""


async def query_transactions(code_insee: str, year_from: int = 2024, year_to: int | None = None) -> dict:
    return {"transactions": [], "median_eur_per_m2": None, "count": 0}
