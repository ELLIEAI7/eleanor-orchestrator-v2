""" 
Runtime Configuration
---------------------
Defines the configuration for the Eleanor runtime loop.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class RuntimeConfig(BaseModel):
    mode: str = "balanced"
    max_concurrent_tasks: int = 10
    decision_timeout: float = 20.0
    healthcheck_interval: float = 30.0
    enable_precedent: bool = True
    enable_telemetry: bool = True
    enable_events: bool = True
    log_level: str = "INFO"
    
    class Config:
        arbitrary_types_allowed = True
