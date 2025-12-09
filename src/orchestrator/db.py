import os
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import aiosqlite

DB_PATH = os.getenv("ELEANOR_DB_PATH", "eleanor.db")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS precedents (
    precedent_id TEXT PRIMARY KEY,
    input_text TEXT NOT NULL,
    outcome TEXT,
    confidence REAL,
    mitigations TEXT,
    critics TEXT,
    flags TEXT,
    tags TEXT,
    severity TEXT,
    audit_hash TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_precedents_created_at ON precedents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_precedents_severity ON precedents(severity);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()


async def store_precedent_db(record: Dict[str, Any]) -> str:
    await init_db()
    precedent_id = record.get("precedentId")
    mitigations = json.dumps(record.get("mitigations", []), ensure_ascii=False)
    critics = json.dumps(record.get("critics", {}), ensure_ascii=False)
    flags = json.dumps(record.get("flags", []), ensure_ascii=False)
    tags = json.dumps(record.get("tags", []), ensure_ascii=False)
    created_at = datetime.utcnow().isoformat() + "Z"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO precedents
            (precedent_id, input_text, outcome, confidence, mitigations, critics, flags, tags, severity, audit_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                precedent_id,
                record.get("input"),
                record.get("outcome"),
                record.get("confidence", 0.0),
                mitigations,
                critics,
                flags,
                tags,
                record.get("severity", "medium"),
                record.get("auditHash"),
                created_at,
            ),
        )
        await db.commit()
    return precedent_id


async def read_precedents_db(limit: Optional[int] = None, sort: str = "newest") -> List[Dict[str, Any]]:
    await init_db()
    order = "DESC" if sort == "newest" else "ASC"
    sql = f"SELECT * FROM precedents ORDER BY created_at {order}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: aiosqlite.Row) -> Dict[str, Any]:
    return {
        "precedentId": row["precedent_id"],
        "input": row["input_text"],
        "outcome": row["outcome"],
        "confidence": row["confidence"],
        "mitigations": json.loads(row["mitigations"] or "[]"),
        "critics": json.loads(row["critics"] or "{}"),
        "flags": json.loads(row["flags"] or "[]"),
        "tags": json.loads(row["tags"] or "[]"),
        "severity": row["severity"],
        "auditHash": row["audit_hash"],
        "timestamp": row["created_at"],
    }


async def get_precedent_db(precedent_id: str) -> Optional[Dict[str, Any]]:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM precedents WHERE precedent_id = ?", (precedent_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return _row_to_dict(row)


async def query_precedents_db(text_query: Optional[str] = None, tag: Optional[str] = None, severity: Optional[str] = None, flag: Optional[str] = None, sort: str = "newest", limit: Optional[int] = None) -> List[Dict[str, Any]]:
    await init_db()
    order = "DESC" if sort == "newest" else "ASC"
    clauses = []
    params = []
    if text_query:
        clauses.append("(input_text LIKE ? OR outcome LIKE ?)")
        tq = f"%{text_query}%"
        params.extend([tq, tq])
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if severity:
        clauses.append("LOWER(severity) = LOWER(?)")
        params.append(severity)
    if flag:
        clauses.append("flags LIKE ?")
        params.append(f"%{flag}%")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM precedents {where} ORDER BY created_at {order}"
    if limit:
        sql += f" LIMIT {int(limit)}"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_dict(r) for r in rows]
