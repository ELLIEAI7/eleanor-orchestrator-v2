# commons/telemetry.py
"""
ELEANOR — Telemetry
-------------------

Centralized telemetry utilities.

Provides:
  • start_span / end_span
  • emit_metric
  • emit_trace
  • critic timing capture
  • fusion timing + uncertainty tracking

Telemetry is emitted using the EventBus so all downstream systems
(analytics, debugging, dashboards) can subscribe.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import time
import uuid
import logging
import asyncio

from .events import get_bus

logger = logging.getLogger("eleanor.telemetry")


async def start_span(
    name: str, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    span_id = str(uuid.uuid4())
    start_time = time.time()

    await (await get_bus()).emit(
        "telemetry.span.start",
        payload={
            "span_id": span_id,
            "name": name,
            "context": context or {},
            "timestamp": start_time,
        },
    )

    return {
        "span_id": span_id,
        "name": name,
        "start": start_time,
        "context": context or {},
    }


async def end_span(span: Dict[str, Any], result: Optional[Any] = None):
    duration = time.time() - span["start"]

    await (await get_bus()).emit(
        "telemetry.span.end",
        payload={
            "span_id": span["span_id"],
            "name": span["name"],
            "duration": duration,
            "result_summary": str(result)[:500] if result else None,
        },
    )


async def emit_metric(
    name: str, value: float, tags: Optional[Dict[str, Any]] = None
):
    await (await get_bus()).emit(
        "telemetry.metric",
        payload={
            "name": name,
            "value": value,
            "tags": tags or {},
        },
    )


async def emit_trace(message: str, details: Optional[Dict[str, Any]] = None):
    await (await get_bus()).emit(
        "telemetry.trace",
        payload={
            "message": message,
            "details": details or {},
        },
    )
