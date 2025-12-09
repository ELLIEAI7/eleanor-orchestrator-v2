# Integration Guide (Standalone Orchestrator v2)

## Running alongside EJE and Commons
- Run this service in its own container/process.
- Commons calls WS `/deliberate/stream` and REST `/health`, `/system/status`, `/precedents*`.
- EJE can consume the same endpoints if needed; no code coupling required.

## Docker
```bash
docker build -t eleanor-orchestrator-v2 .
docker run -p 8000:8000 \
  -e ELEANOR_API_KEY=... \
  -e ELEANOR_WS_AUTH=true \
  -e ELEANOR_DB_PATH=/data/eleanor.db \
  eleanor-orchestrator-v2
```

## docker-compose
See `docker-compose.yml`; envs can be set in `.env`.

## Hardware bundle
- Place this container alongside EJE and Commons; share a network.
- Configure env in the systemd unit or compose file.
- Models (critics) should be available to the adapter (e.g., Ollama) on the same host/network.

## Security defaults
- API key required on REST if `ELEANOR_API_KEY` set; WS auth optional via `ELEANOR_WS_AUTH=true`.
- Rate limiting default 20/min; override with `ELEANOR_RATE_LIMIT`.
- Input/body caps via `ELEANOR_MAX_INPUT`, `ELEANOR_MAX_BODY_BYTES`.
- Disable JSONL fallback in prod: `ELEANOR_JSONL_FALLBACK=false`.

## Compliance profiles
- `ELEANOR_PROFILE=euai` or `nist-high` adjusts thresholds for rights/fairness/risk/truth/pragmatics.
- `ELEANOR_OVERLAY_FILE` for org-specific thresholds/mitigations.

## Persistence
- Primary: SQLite (aiosqlite) at `ELEANOR_DB_PATH` with WAL.
- Optional JSONL fallback (dev) controlled by `ELEANOR_JSONL_FALLBACK`.
- Optional immutable mirror: `ELEANOR_CHAIN_WEBHOOK`.

## Logs & audit
- Structured JSON logging; Request IDs; auditId and auditHash per deliberation.

## Compatibility
- Orchestrator is adapter-based; Ollama adapter included. Swap by writing a new adapter and updating `config.build_adapter()`.
