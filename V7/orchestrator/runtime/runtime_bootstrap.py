""" 
Runtime Bootstrap
-----------------
Creates a fully initialized runtime instance from:
• router
• critics
• fusion engines
• hybrid core
• runtime config
"""

from __future__ import annotations
from typing import Dict, Any

from ..hybrid_core.hybrid_core import HybridCore
from ..hybrid_core.hybrid_modes import HybridMode
from ..fusion.consensus_fusion import ConsensusFusion
from ..fusion.critic_fusion import CriticFusion
from ..fusion.uncertainty_fusion import UncertaintyEngine
from ..fusion.precedent_fusion import PrecedentEngine
from ..router.router import Router
from .runtime import EleanorRuntime
from .runtime_config import RuntimeConfig

async def bootstrap_runtime(
    router: Router,
    critics: Dict[str, Any],
    storage_backend=None,
    config: RuntimeConfig = None,
):
    config = config or RuntimeConfig()
    
    # fusion stack
    critic_fusion = CriticFusion()
    uncertainty = UncertaintyEngine(threshold=config.decision_timeout / 60)
    precedent = PrecedentEngine(storage_backend) if storage_backend else None
    
    fusion = ConsensusFusion(
        critic_fusion=critic_fusion,
        uncertainty_engine=uncertainty,
        precedent_engine=precedent,
    )
    
    hybrid_core = HybridCore(
        router=router,
        critics=critics,
        fusion=fusion,
        mode=HybridMode.get(config.mode),
    )
    
    runtime = EleanorRuntime(
        hybrid=hybrid_core,
        config=config,
    )
    
    return runtime
