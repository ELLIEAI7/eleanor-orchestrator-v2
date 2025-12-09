""" 
eleanor debug request.json
--------------------------
Debug mode — prints each stage of deliberation.
"""

from __future__ import annotations
import json
from pathlib import Path

async def cmd_debug(args):
    data = json.loads(Path(args.input).read_text())
    
    print("=== ELEANOR DEBUG MODE ===")
    print("Request:")
    print(json.dumps(data, indent=2))
    print("\n(Stub) Running critics...")
    print("rights → OK")
    print("risk → OK")
    print("fairness → OK")
    print("truth → OK")
    print("pragmatics → OK")
    print("\nFusion result → proceed")
    print("Uncertainty → 0.12")
    print("Decision → proceed\n")
    print("=== END DEBUG ===")
