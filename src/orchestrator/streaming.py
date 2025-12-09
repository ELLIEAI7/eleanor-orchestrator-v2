import json
from fastapi import WebSocket

async def emit(ws: WebSocket, payload: dict):
    await ws.send_text(json.dumps(payload, default=str))
