# commons/hooks.py
"""
ELEANOR — Hook System
---------------------

Provides lifecycle hooks around all major Eleanor operations:
  • before_router
  • after_router
  • before_critic
  • after_critic
  • before_fusion
  • after_fusion
  • before_runtime_step
  • after_runtime_step

Hooks are async and non-blocking. Failures are isolated so they never crash
the main deliberation path.
"""

from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, List
import asyncio
import logging
import traceback

logger = logging.getLogger("eleanor.hooks")

Hook = Callable[[Dict[str, Any]], Awaitable[None]]


class HookManager:
    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = {
            "before_router": [],
            "after_router": [],
            "before_critic": [],
            "after_critic": [],
            "before_fusion": [],
            "after_fusion": [],
            "before_runtime_step": [],
            "after_runtime_step": [],
        }
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------

    async def register(self, hook_name: str, fn: Hook) -> None:
        async with self._lock:
            if hook_name not in self._hooks:
                raise ValueError(f"Unknown hook: {hook_name}")
            self._hooks[hook_name].append(fn)
        logger.debug(f"[Hooks] Registered hook → {hook_name}")

    # ------------------------------------------------------------------

    async def fire(self, hook_name: str, context: Dict[str, Any]) -> None:
        hooks = self._hooks.get(hook_name, [])
        if not hooks:
            return

        tasks = []
        for fn in hooks:
            tasks.append(asyncio.create_task(self._safe(fn, context)))
        await asyncio.gather(*tasks, return_exceptions=True)

    # ------------------------------------------------------------------

    async def _safe(self, fn: Hook, ctx: Dict[str, Any]):
        try:
            await fn(ctx)
        except Exception as exc:
            logger.error(
                f"[Hooks] Error in hook '{fn}': {exc}\n{traceback.format_exc()}"
            )


# Singleton
_hook_manager = HookManager()


async def get_hooks() -> HookManager:
    return _hook_manager
