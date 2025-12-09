""" 
Hybrid Modes
------------
Defines configuration profiles for Eleanor's operational behavior.

Each mode determines:
• how strictly we enforce lexicographic safeguards
• uncertainty thresholds
• whether escalation is allowed or required
• whether blocking actions are permitted
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class HybridModeConfig:
    name: str
    enforce_lex: bool = True
    allow_override: bool = False
    auto_escalate: bool = True
    uncertainty_threshold: float = 0.35
    block_on_violation: bool = True
    advisory_only: bool = False

class HybridMode:
    """
    Predefined Hybrid Mode Profiles
    """
    
    STRICT = HybridModeConfig(
        name="strict",
        enforce_lex=True,
        allow_override=False,
        auto_escalate=True,
        uncertainty_threshold=0.25,
        block_on_violation=True,
        advisory_only=False,
    )
    
    BALANCED = HybridModeConfig(
        name="balanced",
        enforce_lex=True,
        allow_override=False,
        auto_escalate=True,
        uncertainty_threshold=0.35,
        block_on_violation=True,
        advisory_only=False,
    )
    
    PERMISSIVE = HybridModeConfig(
        name="permissive",
        enforce_lex=False,
        allow_override=True,
        auto_escalate=False,
        uncertainty_threshold=0.50,
        block_on_violation=False,
        advisory_only=False,
    )
    
    ADVISORY = HybridModeConfig(
        name="advisory",
        enforce_lex=False,
        allow_override=True,
        auto_escalate=False,
        uncertainty_threshold=1.0,
        block_on_violation=False,
        advisory_only=True,
    )
    
    APPLIANCE = HybridModeConfig(
        name="appliance",
        enforce_lex=True,
        allow_override=False,
        auto_escalate=True,
        uncertainty_threshold=0.30,
        block_on_violation=True,
        advisory_only=False,
    )
    
    DISTRIBUTED = HybridModeConfig(
        name="distributed",
        enforce_lex=True,
        allow_override=False,
        auto_escalate=True,
        uncertainty_threshold=0.30,
        block_on_violation=True,
        advisory_only=False,
    )
    
    @classmethod
    def get(cls, mode: str) -> HybridModeConfig:
        mode = mode.lower()
        if mode == "strict":
            return cls.STRICT
        if mode == "balanced":
            return cls.BALANCED
        if mode == "permissive":
            return cls.PERMISSIVE
        if mode == "advisory":
            return cls.ADVISORY
        if mode == "appliance":
            return cls.APPLIANCE
        if mode == "distributed":
            return cls.DISTRIBUTED
        raise ValueError(f"Unknown hybrid mode '{mode}'")
