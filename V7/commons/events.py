# commons/events.py
"""
ELEANOR — Event System
----------------------

A lightweight, async event bus used across the runtime, router, fusion
layer, and hybrid core.

Provides:
  • Event types (with structured payloads)
  • Async dispatch with fan-out
  • Listener registration
  • Safe error isolation per-listener
  • Telemetry hooks

This module is production-ready and designed for high-volume internal events
during deliberation.
"""

from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
import asyncio
import logging
import traceback
import uuid
import time

logger = logging.getLogger("eleanor.events")


# ---------------------------------------------------------------------------
# Event Schema
# ---------------------------------------------------------------------------

class Event(BaseModel):
    """
    A structured event dispatched across Eleanor subsystems.

    Fields:
        id: Unique event ID
        name: Event type string
        timestamp: Unix timestamp
        payload: Event-specific data
        metadata: Optional headers (actor, request_id, etc.)
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Event Bus Implementation
# ---------------------------------------------------------------------------

Listener = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    Central async event bus.

    Features:
      • subscribe(event_name, listener)
      • emit(event_name, payload)
      • broadcast(event)

    All listeners are isolated; one crashing never prevents others from running.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Listener]] = {}
        self._lock = asyncio.Lock()

    # ----------------------------------------------------------------------

    async def subscribe(self, event_name: str, listener: Listener) -> None:
        """
        Register a listener callback for a given event.
        """
        async with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(listener)
        logger.debug(f"[EventBus] Subscribed listener to '{event_name}'")

    # ----------------------------------------------------------------------

    async def emit(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Create and dispatch an event to all registered listeners.
        """
        event = Event(
            name=event_name,
            payload=payload or {},
            metadata=metadata or {},
        )
        await self.broadcast(event)
        return event

    # ----------------------------------------------------------------------

    async def broadcast(self, event: Event) -> None:
        """
        Dispatch a pre-constructed event to all listeners.
        """
        listeners = self._listeners.get(event.name, [])
        if not listeners:
            logger.debug(f"[EventBus] No listeners for event '{event.name}'")
            return

        logger.debug(
            f"[EventBus] Broadcasting '{event.name}' → {len(listeners)} listeners"
        )

        tasks = []
        for listener in listeners:
            tasks.append(asyncio.create_task(self._safe_invoke(listener, event)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ----------------------------------------------------------------------

    async def _safe_invoke(self, listener: Listener, event: Event):
        """
        Wrap a listener invocation with robust error handling.
        """
        try:
            await listener(event)
        except Exception as exc:
            logger.error(
                f"[EventBus] Listener error in '{event.name}': {exc}\n{traceback.format_exc()}"
            )


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_event_bus = EventBus()


async def get_bus() -> EventBus:
    return _event_bus


# ---------------------------------------------------------------------------
# Utility Decorator for Listeners
# ---------------------------------------------------------------------------

def listener(event_name: str):
    """
    Decorator for auto-registering a listener function.

    Example:
        @listener("runtime.started")
        async def on_start(event: Event):
            ...
    """
    def decorator(fn: Listener):
        asyncio.create_task(_event_bus.subscribe(event_name, fn))
        return fn
    return decorator
