from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.orchestrator import run as orchestrator_run
from app.security import QueryRequest, limiter, secure_headers

app = FastAPI(title="QuartierScope AI", version="0.1.0", docs_url="/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_secure_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
    response = await call_next(request)
    secure_headers.set_headers(response)
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/query")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def query(request: Request, body: QueryRequest) -> dict:
    result = await orchestrator_run(
        query=body.query,
        history=body.history,
        deal_id=body.deal_id,
    )
    return result
