""" 
Uncertainty Engine
------------------
Computes Eleanor's global uncertainty score.

Inputs (critic outputs):
critics = {
    "rights": {"score": ..., "confidence": ..., ...},
    "risk": {...},
    ...
}

Outputs:
{
    "uncertainty": float,
    "escalate": bool,
    "dispersion": variance,
    "min_confidence": float,
}
"""

from __future__ import annotations
from typing import Dict, Any
import statistics
from commons.telemetry import emit_metric

class UncertaintyEngine:
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
    
    # ---------------------------------------------------------
    
    async def compute(self, critics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        scores = []
        confidences = []
        
        for c in critics.values():
            scores.append(float(c.get("score", 0.0)))
            confidences.append(float(c.get("confidence", 0.0)))
        
        # Statistical disagreement
        dispersion = statistics.pvariance(scores) if len(scores) > 1 else 0.0
        
        # If any critic has low confidence, uncertainty rises
        low_conf = min(confidences) < 0.3
        raw_uncertainty = min(1.0, dispersion * 2.5 + (0.3 if low_conf else 0.0))
        escalate = raw_uncertainty >= self.threshold
        
        await emit_metric("uncertainty.score", raw_uncertainty)
        
        return {
            "uncertainty": raw_uncertainty,
            "escalate": escalate,
            "dispersion": dispersion,
            "min_confidence": min(confidences),
        }
