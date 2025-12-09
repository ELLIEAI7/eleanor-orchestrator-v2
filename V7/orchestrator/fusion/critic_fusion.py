""" 
Critic Fusion
-------------
Implements Eleanor's multi-critic aggregation logic:
• Lexicographic precedence for rights-based critics.
• Weighted multi-objective scoring for the remaining critics.
• Structure-preserving aggregation with full rationale retention.
"""

from __future__ import annotations
from typing import Dict, Any
import logging
from commons.telemetry import start_span, end_span

logger = logging.getLogger("eleanor.critic_fusion")

class CriticFusion:
    """
    Expected critic output format:
    {
        "score": float (0-1),
        "confidence": float (0-1),
        "violation": bool,
        "rationale": str
    }
    
    Fusion output:
    {
        "aggregate_score": float,
        "violations": [...],
        "lex_block": bool,
        "details": { critic_outputs }
    }
    """
    
    RIGHTS_CRITICS = {"rights"}
    DEFAULT_WEIGHTS = {
        "rights": 0.0,  # rights cannot be "weighted"
        "risk": 0.25,
        "fairness": 0.25,
        "truth": 0.25,
        "pragmatics": 0.25,
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    # ---------------------------------------------------------
    
    async def fuse(self, critics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        span = await start_span("fusion.critics")
        
        # 1) Rights-based lexicographic block
        lex_violations = []
        for name, out in critics.items():
            if name in self.RIGHTS_CRITICS and out.get("violation", False):
                lex_violations.append(name)
        
        if lex_violations:
            result = {
                "aggregate_score": 0.0,
                "violations": lex_violations,
                "lex_block": True,
                "details": {"critic_outputs": critics},
            }
            await end_span(span, result=result)
            return result
        
        # 2) Weighted scoring
        total = 0.0
        for name, out in critics.items():
            w = self.weights.get(name, 0.0)
            score = float(out.get("score", 0.0))
            total += w * score
        
        result = {
            "aggregate_score": total,
            "violations": [],
            "lex_block": False,
            "details": {"critic_outputs": critics},
        }
        await end_span(span, result=result)
        return result      
