from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .security import MAX_BODY_BYTES

class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # For WebSocket, skip
        if request.scope.get("type") == "websocket":
            return await call_next(request)
        # Enforce content-length if present
        cl = request.headers.get("content-length")
        if cl and int(cl) > MAX_BODY_BYTES:
            return Response(status_code=413, content="Payload too large")
        # For streamed bodies, Starlette buffers by default; rely on content-length header
        return await call_next(request)
