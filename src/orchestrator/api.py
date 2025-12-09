import os
from fastapi import FastAPI, WebSocket, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .engine import orchestrate
from .config import settings
from .schemas import Health, SystemStatus, PrecedentRecord
from .utils import gpu_utilization, MAX_INPUT_CHARS
from .precedent import read_precedents, get_precedent, query_precedents
from .db import read_precedents_db, get_precedent_db, query_precedents_db
from .security import require_api_key, WS_AUTH_REQUIRED
from .logging_setup import configure_logging
from .limits import limiter
from .request_id import RequestIdMiddleware
from .body_limit import BodySizeLimitMiddleware

logger = configure_logging()

app = FastAPI(title="ELEANOR Orchestrator v2 (Standalone)")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ELEANOR_CORS_ALLOW", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=Health)
async def health(_=Depends(require_api_key)):
    return {"status": "ok"}


@app.get("/system/status", response_model=SystemStatus)
@limiter.limit("30/minute")
async def system_status(request: Request, _=Depends(require_api_key)):
    try:
        import psutil
        cpu = int(psutil.cpu_percent())
        ram = int(psutil.virtual_memory().percent)
    except Exception:
        cpu = ram = 0
    gpu = gpu_utilization() or 0
    return {
        "cpu": cpu,
        "ram": ram,
        "gpu": gpu,
        "models": [
            {"name": name, "model": model, "loaded": True}
            for name, model in settings.MODELS.items()
        ],
    }


@app.websocket("/deliberate/stream")
async def deliberation_stream(ws: WebSocket):
    await ws.accept()
    headers = dict(ws.headers)
    queries = dict(ws.query_params)
    if WS_AUTH_REQUIRED:
        from .security import validate_ws_api_key
        if not validate_ws_api_key(headers, queries):
            await ws.send_json({"error": "Unauthorized"})
            await ws.close(code=1008)
            return

    try:
        start_msg = await ws.receive_json()
    except Exception:
        await ws.send_json({"error": "Invalid JSON payload"})
        await ws.close(code=1003)
        return

    user_input = start_msg.get("input", "")
    if not user_input or len(str(user_input)) > MAX_INPUT_CHARS:
        await ws.send_json({"error": "Input missing or too large"})
        await ws.close(code=1003)
        return

    adapter = settings.build_adapter()
    await orchestrate(ws, user_input, adapter)
    await ws.close()


@app.get("/precedents", response_model=list[PrecedentRecord])
@limiter.limit("20/minute")
async def list_precedents(request: Request, _=Depends(require_api_key)):
    try:
        records = await read_precedents_db()
    except Exception:
        records = read_precedents()
    return records


@app.get("/precedents/{precedent_id}", response_model=PrecedentRecord | None)
@limiter.limit("40/minute")
async def fetch_precedent(precedent_id: str, request: Request, _=Depends(require_api_key)):
    try:
        rec = await get_precedent_db(precedent_id)
    except Exception:
        rec = get_precedent(precedent_id)
    return rec


@app.post("/precedents/query", response_model=list[PrecedentRecord])
@limiter.limit("20/minute")
async def search_precedents(payload: dict, request: Request, _=Depends(require_api_key)):
    text_query = payload.get("q") or payload.get("query")
    tag = payload.get("tag")
    severity = payload.get("severity")
    flag = payload.get("flag")
    sort = payload.get("sort")  # "newest" | "oldest" | None
    limit = payload.get("limit")
    try:
        records = await query_precedents_db(text_query, tag=tag, severity=severity, flag=flag, sort=sort or "newest", limit=limit)
    except Exception:
        records = query_precedents(text_query, tag=tag, severity=severity, flag=flag)
    if sort == "newest":
        records = sorted(records, key=lambda r: r.timestamp, reverse=True)
    elif sort == "oldest":
        records = sorted(records, key=lambda r: r.timestamp)
    if isinstance(limit, int) and limit > 0:
        records = records[:limit]
    return records
