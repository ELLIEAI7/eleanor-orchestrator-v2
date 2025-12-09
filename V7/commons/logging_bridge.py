# commons/logging_bridge.py
"""
ELEANOR — Logging Bridge
------------------------

Provides structured JSON logging + bridges logs into the EventBus so they can
be inspected by observability tools.

Works seamlessly with the runtime, router, critics, and fusion engine.
"""

from __future__ import annotations
from typing import Any, Dict
import logging
import json
import time
import asyncio

from .events import get_bus


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": time.time(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data)


class EventLogHandler(logging.Handler):
    """
    Sends all logs into the EventBus for consumption by dashboards, console
    loggers, or distributed observability.
    """

    def __init__(self):
        super().__init__()

    def emit(self, record: logging.LogRecord):
        try:
            payload = {
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": time.time(),
                "logger": record.name,
            }
            asyncio.create_task(
                (await get_bus()).emit("log.record", payload=payload)
            )
        except Exception:
            pass  # Never break logging


def init_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    # EventLogHandler is optional but recommended
    root.addHandler(EventLogHandler())
