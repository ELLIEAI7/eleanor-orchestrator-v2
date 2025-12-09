from typing import List, Dict, Optional
from pydantic import BaseModel
import time


class DeliberationStart(BaseModel):
    type: str = "start"
    input: str


class DeliberationEvent(BaseModel):
    type: str = "deliberation_event"
    critic: str
    message: str
    confidence: float
    timestamp: float = time.time()


class ConflictEvent(BaseModel):
    type: str = "conflict"
    critic: str
    severity: str
    message: str
    timestamp: float = time.time()


class CriticBreakdown(BaseModel):
    summary: str
    details: List[str]
    confidence: float


class FinalDecision(BaseModel):
    type: str = "final_decision"
    outcome: str
    confidence: float
    mitigations: List[str]
    criticBreakdown: Dict[str, CriticBreakdown]
    precedentId: Optional[str] = None
    flags: List[str] = []
    severity: str = "medium"  # low | medium | high
    auditId: Optional[str] = None
    auditHash: Optional[str] = None


class SystemStatus(BaseModel):
    cpu: int
    ram: int
    gpu: int
    models: List[Dict[str, str]]


class Health(BaseModel):
    status: str = "ok"


class PrecedentRecord(BaseModel):
    precedentId: str
    input: str
    outcome: str
    confidence: float
    mitigations: List[str]
    critics: Dict[str, Dict]
    timestamp: int
    flags: List[str] = []
    tags: List[str] = []
    severity: str = "medium"
    auditId: Optional[str] = None
    auditHash: Optional[str] = None
