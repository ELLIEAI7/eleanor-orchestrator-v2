import json
import os
import time
from typing import Dict, Any, List, Optional
from .schemas import PrecedentRecord
from .db import store_precedent_db, read_precedents_db, get_precedent_db, query_precedents_db

PRECEDENT_FILE = os.getenv("ELEANOR_PRECEDENT_FILE", "precedents.jsonl")
CHAIN_WEBHOOK = os.getenv("ELEANOR_CHAIN_WEBHOOK")  # optional: POST precedent to a blockchain gateway
JSONL_FALLBACK = os.getenv("ELEANOR_JSONL_FALLBACK", "true").lower() == "true"


def _ensure_file():
    os.makedirs(os.path.dirname(PRECEDENT_FILE) or ".", exist_ok=True)
    if not os.path.exists(PRECEDENT_FILE):
        with open(PRECEDENT_FILE, "w", encoding="utf-8"):
            pass


def store_precedent(record: Dict[str, Any]) -> str:
    """Append a precedent record to a JSONL file and return the generated ID."""
    case_id = record.get("precedentId") or f"EC-{int(time.time())}"
    record["precedentId"] = case_id
    if JSONL_FALLBACK:
        _ensure_file()
        with open(PRECEDENT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    # Also persist to sqlite db (best effort)
    try:
        import asyncio
        asyncio.run(store_precedent_db(record))
    except Exception:
        pass
    # Optional: forward to a blockchain gateway / webhook for immutable storage
    if CHAIN_WEBHOOK:
        try:
            import requests
            requests.post(CHAIN_WEBHOOK, json=record, timeout=5)
        except Exception:
            # Best-effort; do not fail the main path
            pass
    return case_id


def read_precedents() -> List[PrecedentRecord]:
    try:
        # prefer DB if available
        import asyncio
        rows = asyncio.run(read_precedents_db())
        return [PrecedentRecord(**r) for r in rows]
    except Exception:
        pass
    if not JSONL_FALLBACK:
        return []
    _ensure_file()
    records: List[PrecedentRecord] = []
    with open(PRECEDENT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(PrecedentRecord(**data))
            except Exception:
                continue
    return records


def get_precedent(precedent_id: str) -> Optional[PrecedentRecord]:
    for rec in read_precedents():
        if rec.precedentId == precedent_id:
            return rec
    return None


def query_precedents(text_query: Optional[str] = None, tag: Optional[str] = None, severity: Optional[str] = None, flag: Optional[str] = None) -> List[PrecedentRecord]:
    records = read_precedents()
    if text_query:
        q = text_query.lower()
        records = [
            rec for rec in records
            if q in (rec.input or "").lower()
            or q in (rec.outcome or "").lower()
            or any(q in (tag.lower()) for tag in (rec.tags or []))
        ]
    if tag:
        records = [rec for rec in records if any(tag.lower() == t.lower() for t in (rec.tags or []))]
    if severity:
        records = [rec for rec in records if rec.severity.lower() == severity.lower()]
    if flag:
        records = [rec for rec in records if flag.lower() in [f.lower() for f in (rec.flags or [])]]
    return records
