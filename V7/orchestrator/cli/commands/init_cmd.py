""" 
eleanor init
------------
Creates a starter Eleanor project:
• runtime_config.yaml
• sample input
• folder structure
"""

from __future__ import annotations
from pathlib import Path
import json
import os

def cmd_init(args):
    out = Path(args.dir)
    out.mkdir(parents=True, exist_ok=True)
    
    # sample config
    config = {
        "mode": "balanced",
        "max_concurrent_tasks": 10,
        "decision_timeout": 20.0,
    }
    (out / "runtime_config.json").write_text(json.dumps(config, indent=2))
    
    # sample request file
    (out / "sample_request.json").write_text(
        json.dumps(
            {"task": "general_request", "input": "Hello world"},
            indent=2,
        )
    )
    
    print(f"Initialized Eleanor project in: {out.absolute()}")
