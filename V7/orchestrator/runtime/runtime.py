""" 
Eleanor Runtime
---------------
High-level operational shell around the hybrid core.

Responsibilities:
• concurrency mgmt
• lifecycle management
• timeouts
• event + telemetry emission
• public async API for decision requests
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import asyncio
import logging

from commons.events import get_bus
from commons.hooks import get_hooks
from commons.telemetry import start_span, end_span, emit_trace
from .runtime_state import RuntimeState
from .runtime_config import RuntimeConfig
from ..hybrid_core.hybrid_exceptions import EscalationRequired

logger = logging.getLogger("eleanor.runtime")

class EleanorRuntime:
    def __init__(self, hybrid, config: RuntimeConfig):
        self.hybrid = hybrid
        self.config = config
        self.state = RuntimeState()
        self.semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
    
    # ------------------------------------------------------------------
    
    async def decide(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Top-level API:
        result = await runtime.decide(request)
        """
        req_id = self.state.new_request_id()
        self.state.log_request(req_id, request)
        
        hooks = await get_hooks()
        bus = await get_bus()
        
        await bus.emit("runtime.request.received", {"id": req_id, "request": request})
        await hooks.fire("before_runtime_step", {"id": req_id, "request": request})
        
        span = await start_span("runtime.decide", {"req_id": req_id})
        
        async with self.semaphore:
            try:
                self.state.increment_active()
                
                result = await asyncio.wait_for(
                    self.hybrid.deliberate(request),
                    timeout=self.config.decision_timeout,
                )
                
                self.state.complete()
                await hooks.fire("after_runtime_step", {"id": req_id, "result": result})
                await bus.emit("runtime.request.completed", {"id": req_id, "result": result})
                await end_span(span, result=result)
                
                return result
            
            except EscalationRequired as exc:
                self.state.fail()
                await emit_trace("runtime.escalation", {"id": req_id})
                await bus.emit("runtime.request.escalation", {"id": req_id})
                await end_span(span, result="escalation_required")
                
                return {
                    "action": "escalate",
                    "reason": str(exc),
                    "id": req_id,
                }
            
            except Exception as exc:
                self.state.fail()
                logger.error(f"[Runtime] Execution failed: {exc}")
                await emit_trace("runtime.error", {"id": req_id, "error": str(exc)})
                await bus.emit("runtime.request.error", {"id": req_id, "error": str(exc)})
                await end_span(span, result="error")
                
                return {
                    "action": "error",
                    "error": str(exc),
                    "id": req_id,
                }
            
            finally:
                self.state.decrement_active()
