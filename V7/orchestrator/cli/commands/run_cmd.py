""" 
eleanor run input.json
----------------------
Runs a single request through Eleanor.
"""

from __future__ import annotations
import json
from pathlib import Path
from orchestrator.runtime.runtime_bootstrap import bootstrap_runtime
from orchestrator.runtime.runtime_config import RuntimeConfig
from orchestrator.router.router import Router
from orchestrator.router.router_config import RouterConfig

async def cmd_run(args):
    data = json.loads(Path(args.input).read_text())
    
    # Load config
    cfg = None
    if args.config:
        cfg = RuntimeConfig.parse_file(args.config)
    else:
        cfg = RuntimeConfig()
    
    # minimal router config
    router_cfg = RouterConfig(
        default_model="mock",
        models={"mock": {"name": "mock", "endpoint": "", "timeout": 10, "max_retries": 0}},
        routing_rules=[],
    )
    router = Router(router_cfg)
    
    # critics stub
    critics = {
        "rights": FakeCritic("rights"),
        "risk": FakeCritic("risk"),
        "fairness": FakeCritic("fairness"),
        "truth": FakeCritic("truth"),
        "pragmatics": FakeCritic("pragmatics"),
    }
    
    runtime = await bootstrap_runtime(router, critics, storage_backend=None, config=cfg)
    result = await runtime.decide(data)
    
    print(json.dumps(result, indent=2))

# Fake critic used for CLI demonstration
class FakeCritic:
    def __init__(self, name):
        self.name = name
    
    async def evaluate(self, request, backend_result):
        return {
            "score": 0.75,
            "confidence": 0.9,
            "violation": False,
            "rationale": f"{self.name} critic stub.",
        }
