""" 
Eleanor CLI
-----------
Unified command-line interface for:
• init
• run
• diagnose
• evaluate
• debug
"""

from __future__ import annotations
import argparse
import asyncio
import json
import sys
from pathlib import Path

from .commands.init_cmd import cmd_init
from .commands.run_cmd import cmd_run
from .commands.diagnose_cmd import cmd_diagnose
from .commands.evaluate_cmd import cmd_evaluate
from .commands.debug_cmd import cmd_debug

def main():
    parser = argparse.ArgumentParser(
        prog="eleanor",
        description="Eleanor Constitutional Reasoning Engine CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    
    # init
    init_p = sub.add_parser("init", help="Initialize an Eleanor runtime template.")
    init_p.add_argument("--dir", default="eleanor_project", help="Output directory.")
    
    # run
    run_p = sub.add_parser("run", help="Run a single deliberation.")
    run_p.add_argument("input", help="Path to JSON input file.")
    run_p.add_argument("--config", help="Runtime config file.", default=None)
    
    # diagnose
    diag_p = sub.add_parser("diagnose", help="Run system diagnostics.")
    
    # evaluate
    eval_p = sub.add_parser("evaluate", help="Run evaluation suite.")
    eval_p.add_argument("path", help="Directory of test cases.")
    
    # debug
    debug_p = sub.add_parser("debug", help="Debug a single request interactively.")
    debug_p.add_argument("input", help="Path to JSON input.")
    
    args = parser.parse_args()
    
    # dispatch
    if args.command == "init":
        cmd_init(args)
    elif args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "diagnose":
        asyncio.run(cmd_diagnose(args))
    elif args.command == "evaluate":
        asyncio.run(cmd_evaluate(args))
    elif args.command == "debug":
        asyncio.run(cmd_debug(args))
    else:
        parser.print_help()
        sys.exit(1)
