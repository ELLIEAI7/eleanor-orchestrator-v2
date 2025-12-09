# commons/registry.py
"""
ELEANOR — Registry
------------------

A central plugin/extension registry for:
  • critics
  • fusion strategies
  • router backends
  • hybrid modes

Allows dynamic discovery by name or type.

Used throughout the orchestrator and runtime.
"""

from typing import Any, Callable, Dict
import logging

logger = logging.getLogger("eleanor.registry")


class Registry:
    def __init__(self):
        self._items: Dict[str, Any] = {}

    def register(self, name: str, item: Any):
        if name in self._items:
            logger.warning(f"[Registry] Overwriting existing item: {name}")
        self._items[name] = item
        logger.debug(f"[Registry] Registered item '{name}' → {item}")

    def get(self, name: str) -> Any:
        if name not in self._items:
            raise KeyError(f"Registry has no item named '{name}'")
        return self._items[name]

    def all(self) -> Dict[str, Any]:
        return dict(self._items)


# Singleton registry
registry = Registry()
