""" 
Runtime State
-------------
Holds ephemeral, non-persistent runtime counters, timestamps,
and other execution metadata.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any
import time
import uuid

@dataclass
class RuntimeState:
    boot_time: float = field(default_factory=time.time)
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_healthcheck: float = field(default_factory=time.time)
    request_log: Dict[str, Any] = field(default_factory=dict)
    
    def new_request_id(self) -> str:
        return str(uuid.uuid4())
    
    def log_request(self, req_id: str, payload: Any):
        self.request_log[req_id] = {
            "payload": payload,
            "timestamp": time.time(),
        }
    
    def increment_active(self):
        self.active_tasks += 1
    
    def decrement_active(self):
        self.active_tasks = max(0, self.active_tasks - 1)
    
    def complete(self):
        self.completed_tasks += 1
    
    def fail(self):
        self.failed_tasks += 1
