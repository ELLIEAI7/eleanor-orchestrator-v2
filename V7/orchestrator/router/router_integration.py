# orchestrator/router/router_integration.py
"""
Router Integration Utilities
----------------------------

Helps load router config from YAML/JSON and instantiate Router().
"""

from __future__ import annotations
from typing import Any, Dict
import yaml

from .router import Router
from .router_config import RouterConfig


def load_router_from_config(path: str) -> Router:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    cfg = RouterConfig.from_dict(raw)
    return Router(cfg)
