""" 
Precedent Fusion Engine
-----------------------
Retrieves similar historical cases from storage and evaluates their relevance.

storage_backend must implement:
async search_embeddings(vector, top_k=5) -> List[precedents]
"""

from __future__ import annotations
from typing import Any, Dict, List
import logging
from commons.telemetry import start_span, end_span, emit_trace

logger = logging.getLogger("eleanor.precedent")

class PrecedentEngine:
    def __init__(self, storage_backend):
        self.storage = storage_backend
    
    # ---------------------------------------------------------
    
    async def fetch_relevant(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        span = await start_span("precedent.fetch", {"top_k": top_k})
        try:
            results = await self.storage.search_embeddings(vector, top_k=top_k)
            await end_span(span, result={"count": len(results)})
            return results
        except Exception as exc:
            logger.warning(f"[Precedent] Storage error: {exc}")
            await emit_trace("precedent.error", {"error": str(exc)})
            await end_span(span, result="error")
            return []
