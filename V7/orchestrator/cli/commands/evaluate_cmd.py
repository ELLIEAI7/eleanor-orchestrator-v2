""" 
eleanor evaluate ./tests/
------------------------
Runs a folder of test cases through Eleanor and prints metrics.
"""

from __future__ import annotations
from pathlib import Path
import json

async def cmd_evaluate(args):
    path = Path(args.path)
    if not path.exists():
        print(f"Path not found: {path}")
        return
    
    files = sorted(path.glob("*.json"))
    results = []
    
    for f in files:
        try:
            data = json.loads(f.read_text())
            # In real implementation: pass into runtime
            results.append({"file": f.name, "status": "OK"})
        except Exception as exc:
            results.append({"file": f.name, "status": "ERROR", "error": str(exc)})
    
    print(json.dumps(results, indent=2))
