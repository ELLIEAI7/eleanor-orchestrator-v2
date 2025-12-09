""" 
Hybrid Core
-----------
Coordinates:
• router
• critics
• fusion engines
• hybrid mode configuration

Provides a unified async API:
result = await core.deliberate(input)
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import logging
import asyncio

from commons.telemetry import start_span, end_span, emit_trace
from commons.events import get_bus
from .hybrid_modes import HybridMode, HybridModeConfig
from .hybrid_exceptions import EscalationRequired, HybridCoreError

logger = logging.getLogger("eleanor.hybridcore")

class HybridCore:
    def __init__(self, router, critics: Dict[str, Any], fusion, mode: HybridModeConfig = HybridMode.BALANCED):
        """
        router: Router instance
        critics: dict of critic_name → critic_instance
        fusion: ConsensusFusion instance
        mode: HybridModeConfig
        """
        self.router = router
        self.critics = critics
        self.fusion = fusion
        self.mode = mode
    
    # ----------------------------------------------------------------------
    
    async def deliberate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a full constitutional deliberation.
        
        Steps:
        1. route → model backend
        2. get model output
        3. run critics
        4. fuse results
        5. apply mode logic
        """
        span = await start_span("hybrid.deliberate")
        try:
            # ------------------------------
            # Step 1 — router executes model
            # ------------------------------
            backend_result = await self.router.execute(
                request,
                backend_runner=self._backend_runner,
                context=request,
            )
            
            # ------------------------------
            # Step 2 — run critics in parallel
            # ------------------------------
            critics_out = await self._evaluate_critics(request, backend_result)
            
            # ------------------------------
            # Step 3 — fusion
            # ------------------------------
            vector = backend_result.get("embedding")  # optional
            fusion_out = await self.fusion.decide(critics_out, vector=vector)
            
            # ------------------------------
            # Step 4 — hybrid mode logic
            # ------------------------------
            decision = await self._apply_mode(fusion_out)
            
            await end_span(span, result=decision)
            return decision
        
        except EscalationRequired:
            await emit_trace("hybrid.escalation_forced", {"request": request})
            await end_span(span, result="escalation_required")
            raise
        except Exception as exc:
            await emit_trace("hybrid.error", {"error": str(exc)})
            await end_span(span, result="error")
            raise HybridCoreError(str(exc))
    
    # ----------------------------------------------------------------------
    
    async def _backend_runner(self, model_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        For now, this is a placeholder.
        In production, this is replaced by a pluggable backend driver that connects to:
        • local model
        • remote LLM endpoint
        • appliance-embedded model
        """
        raise NotImplementedError("Attach your backend LLM driver here.")
    
    # ----------------------------------------------------------------------
    
    async def _evaluate_critics(self, request, backend_response):
        """
        Run all critics concurrently.
        """
        tasks = {
            name: asyncio.create_task(critic.evaluate(request, backend_response))
            for name, critic in self.critics.items()
        }
        
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as exc:
                logger.warning(f"[HybridCore] Critic '{name}' failed: {exc}")
                results[name] = {
                    "score": 0,
                    "confidence": 0,
                    "violation": False,
                    "rationale": f"Critic error: {exc}",
                }
        
        return results
    
    # ----------------------------------------------------------------------
    
    async def _apply_mode(self, fusion_out: Dict[str, Any]) -> Dict[str, Any]:
        """
        Governs how the system treats the fusion result.
        """
        # Lex block → always block
        if fusion_out.get("lex_block", False):
            if self.mode.enforce_lex:
                return {
                    "action": "reject",
                    "reason": "rights_violation",
                    "fusion": fusion_out,
                }
        
        # Advisory mode → never block or escalate
        if self.mode.advisory_only:
            return {
                "action": "advice",
                "fusion": fusion_out,
            }
        
        # Escalation trigger
        if fusion_out["action"] == "escalate":
            if self.mode.auto_escalate:
                raise EscalationRequired("Uncertainty threshold exceeded.")
        
        # Otherwise return normal fusion decision
        return fusion_out
