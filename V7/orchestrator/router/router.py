# orchestrator/router/router.py
"""
Router
------

Routes requests to the correct model backend.

Features:
  • rule-based routing
  • fallback logic
  • async model execution
  • retries + timeouts
  • telemetry instrumentation
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import asyncio
import logging
import traceback

from commons.telemetry import start_span, end_span, emit_trace
from commons.events import get_bus

from .router_config import RouterConfig
from .router_rules import evaluate_rules
from .router_exceptions import RouterError, NoModelAvailable

logger = logging.getLogger("eleanor.router")


class Router:
    def __init__(self, config: RouterConfig):
        self.config = config
        self.models = config.models

    # ------------------------------------------------------------------

    async def route(self, request: Dict[str, Any]) -> str:
        """
        Determine the backend model to use.
        """
        model = evaluate_rules(self.config.routing_rules, request)
        if model:
            return model
        # default fallback
        return self.config.default_model

    # ------------------------------------------------------------------

    async def execute(
        self,
        request: Dict[str, Any],
        backend_runner: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a routed model call with retries + fallback.

        backend_runner(model_name, request) must be provided externally.
        """
        span = await start_span("router.execute", context)

        try:
            model = await self.route(request)
            cfg = self.config.get_backend(model)

            if not cfg.enabled:
                raise NoModelAvailable(f"Model '{model}' is disabled")

            response = await self._run_backend(cfg, backend_runner, request)
            await end_span(span, result=response)
            return response

        except NoModelAvailable:
            await emit_trace("router.no_model_available", {"request": request})
            await end_span(span, result="fallback_no_model")
            raise

        except Exception as exc:
            logger.error(
                f"[Router] Execution failed: {exc}\n{traceback.format_exc()}"
            )
            await emit_trace("router.error", {"error": str(exc)})
            await end_span(span, result="error")
            raise RouterError(str(exc))

    # ------------------------------------------------------------------

    async def _run_backend(self, cfg, runner, request):
        """
        Run the backend with timeouts + retry logic.
        """
        last_exc = None

        for _ in range(cfg.max_retries + 1):
            try:
                return await asyncio.wait_for(
                    runner(cfg.name, request),
                    timeout=cfg.timeout,
                )
            except Exception as exc:
                last_exc = exc
                await emit_trace(
                    "router.backend_retry",
                    {"backend": cfg.name, "error": str(exc)},
                )

        raise RouterError(
            f"Backend '{cfg.name}' failed after {cfg.max_retries} retries: {last_exc}"
        )
