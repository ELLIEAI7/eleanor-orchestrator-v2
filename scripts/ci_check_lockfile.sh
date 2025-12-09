#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
if [ ! -f requirements-lock.txt ]; then
  echo "requirements-lock.txt missing" >&2
  exit 1
fi
pip install --dry-run -r requirements-lock.txt >/dev/null
echo "Lockfile check passed."
