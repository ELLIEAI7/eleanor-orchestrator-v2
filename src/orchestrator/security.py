import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("ELEANOR_API_KEY")
WS_AUTH_REQUIRED = os.getenv("ELEANOR_WS_AUTH", "false").lower() == "true"
MAX_BODY_BYTES = int(os.getenv("ELEANOR_MAX_BODY_BYTES", "100000"))  # ~100KB default

async def require_api_key(x_api_key: str = Header(None)):
    if API_KEY:
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


def validate_ws_api_key(headers: dict, query_params: dict) -> bool:
    """
    Basic WS auth: accept API key from header `x-api-key` or query param `api_key`.
    """
    if not API_KEY:
        return True
    header_key = headers.get("x-api-key")
    query_key = query_params.get("api_key")
    return API_KEY in {header_key, query_key}
