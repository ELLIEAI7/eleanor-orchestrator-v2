""" 
Hybrid Core Exceptions
----------------------
Defines the exception model for mode switching, uncertainty escalation,
and constitutional constraint violations.
"""

class HybridCoreError(Exception):
    """Generic hybrid core failure."""

class EscalationRequired(HybridCoreError):
    """
    Raised when uncertainty or lexicographic constraints require
    human supervision.
    """

class ModeError(HybridCoreError):
    """Raised when an invalid or unsupported mode is requested."""
