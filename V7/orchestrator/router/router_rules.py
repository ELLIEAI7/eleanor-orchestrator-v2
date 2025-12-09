# orchestrator/router/router_rules.py
"""
Routing Rules
-------------

Evaluates routing rules against an input request.

Rule format (example):
  {
    "if": {"task": "summarize"},
    "use_model": "gpt-4"
  }
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from .router_exceptions import RoutingRuleError


def rule_matches(rule: Dict[str, Any], request: Dict[str, Any]) -> bool:
    """
    Basic property match: rule["if"] = {"task": "summarize"}
    """
    cond = rule.get("if", {})
    if not cond:
        return False

    for key, value in cond.items():
        if request.get(key) != value:
            return False

    return True


def evaluate_rules(rules: list, request: Dict[str, Any]) -> Optional[str]:
    """
    Return the model selected by the first matching rule.
    """
    for rule in rules:
        try:
            if rule_matches(rule, request):
                return rule.get("use_model")
        except Exception as exc:
            raise RoutingRuleError(f"Error evaluating rule {rule}: {exc}")
    return None
