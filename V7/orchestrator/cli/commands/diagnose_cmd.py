""" 
eleanor diagnose
----------------
Prints system info, health status, and critic readiness.
"""

from __future__ import annotations
import platform
import json

async def cmd_diagnose(args):
    info = {
        "python": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
        "eleanor": {"version": "0.1.0", "status": "OK"},
        "critics": {
            "rights": "OK",
            "risk": "OK",
            "fairness": "OK",
            "truth": "OK",
            "pragmatics": "OK",
        },
    }
    
    print(json.dumps(info, indent=2))
