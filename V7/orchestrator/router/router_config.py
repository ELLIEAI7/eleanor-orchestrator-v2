# orchestrator/router/router_config.py
"""
Router Configuration
--------------------

Defines RouterConfig, which controls:
  • available models
  • routing rules
  • timeouts
  • retry/fallback strategies
  • default model
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ModelBackendConfig(BaseModel):
    name: str
    endpoint: str
    timeout: float = 10.0
    max_retries: int = 1
    enabled: bool = True


class RouterConfig(BaseModel):
    default_model: str
    models: Dict[str, ModelBackendConfig]
    routing_rules: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(**data)

    def get_backend(self, name: str) -> ModelBackendConfig:
        if name not in self.models:
            raise KeyError(f"Unknown model backend: {name}")
        return self.models[name]
