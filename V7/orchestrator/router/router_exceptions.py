# orchestrator/router/router_exceptions.py
"""
Router Exceptions
-----------------

Custom errors raised by the router subsystem.
"""


class RouterError(Exception):
    """Base router exception."""


class NoModelAvailable(RouterError):
    """Raised when no backend model is available or healthy."""


class RoutingRuleError(RouterError):
    """Raised when routing rule evaluation fails."""
