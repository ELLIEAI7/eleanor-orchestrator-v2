# Eleanor Orchestrator v2 (Standalone)

Hardened, adapter-based governance engine for Eleanor Logic Core. Features:
- WebSocket streaming deliberation (5 critics, parallel)
- UDHR/UNESCO-aligned prompts/mitigations; protected-class/consent checks
- Auth (API key), optional WS auth, rate limiting, input/body caps
- SQLite (WAL) precedents (JSONL fallback optional), auditId + auditHash
- Optional blockchain/webhook mirror
- Compliance profiles (EU AI Act, NIST high-risk) via env
- Structured JSON logging, Request ID middleware
- Portable adapter layer (Ollama today, swappable backends)

## Quick start
```bash
pip install -r requirements.txt
uvicorn orchestrator.api:app --host 0.0.0.0 --port 8000
```

## Endpoints
- WS: `/deliberate/stream` (send `{ "input": "..." }`)
- REST: `/health`, `/system/status`, `/precedents`, `/precedents/{id}`, `/precedents/query`

## Env toggles (non-exhaustive)
- Security: `ELEANOR_API_KEY`, `ELEANOR_WS_AUTH`, `ELEANOR_RATE_LIMIT`, `ELEANOR_CORS_ALLOW`, `ELEANOR_MAX_INPUT`, `ELEANOR_MAX_BODY_BYTES`
- Compliance: `ELEANOR_PROFILE` (euai | nist-high), `ELEANOR_OVERLAY_FILE`
- Persistence: `ELEANOR_DB_PATH`, `ELEANOR_JSONL_FALLBACK`, `ELEANOR_CHAIN_WEBHOOK`

## Hardware bundle
Run this service alongside EJE and Commons on the same box or container stack. Preconfigure env, models, and critics, and expose orchestrator WS/REST to Commons/EJE.

## Repo scripts
- `scripts/sync_from_dev.sh`: sync code from a dev orchestrator dir into this repo.
- `scripts/ci_check_lockfile.sh`: verify lockfile installability.
- `scripts/ci_body_limit_note.md`: notes for enforcing body-size limits at proxy.

## CI
- `.github/workflows/ci.yml` runs lockfile check and API import.
- `scripts/ci_check_lockfile.sh` validates requirements-lock.txt.
