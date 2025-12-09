""" 
Consensus Fusion Engine
-----------------------
Produces the final constitutional decision result.

Steps:
1. Fuse critic outputs
2. Pull precedent cases (optional)
3. Compute uncertainty
4. Assemble final decision with escalation logic
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import logging
from commons.telemetry import start_span, end_span, emit_trace

logger = logging.getLogger("eleanor.consensus")

class ConsensusFusion:
    def __init__(self, critic_fusion, uncertainty_engine, precedent_engine=None):
        self.critic_fusion = critic_fusion
        self.uncertainty = uncertainty_engine
        self.precedent = precedent_engine
    
    # ---------------------------------------------------------
    
    async def decide(self, critics: Dict[str, Dict[str, Any]], vector: Optional[List[float]] = None) -> Dict[str, Any]:
        span = await start_span("fusion.consensus")
        
        # 1. Critic Fusion
        critic_out = await self.critic_fusion.fuse(critics)
        
        # Rights violation → immediate block
        if critic_out["lex_block"]:
            decision = {
                "action": "reject",
                "confidence": 1.0,
                "uncertainty": 0.0,
                "lex_block": True,
                "rationale": "Rights-critical violation detected.",
                "precedent": [],
            }
            await end_span(span, result=decision)
            return decision
        
        # 2. Precedent Fetch
        precedents = []
        if self.precedent and vector is not None:
            precedents = await self.precedent.fetch_relevant(vector)
        
        # 3. Uncertainty
        unc = await self.uncertainty.compute(critics)
        
        # 4. Final Assembly
        decision = {
            "action": "escalate" if unc["escalate"] else "proceed",
            "confidence": critic_out["aggregate_score"],
            "uncertainty": unc["uncertainty"],
            "lex_block": False,
            "rationale": "Decision derived from Eleanor's multi-critic fusion logic.",
            "precedent": precedents,
        }
        
        if unc["escalate"]:
            await emit_trace("fusion.escalate", {"score": unc["uncertainty"]})
        
        await end_span(span, result=decision)
        return decision
