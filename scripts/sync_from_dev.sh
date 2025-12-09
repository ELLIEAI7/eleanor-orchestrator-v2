#!/usr/bin/env bash
set -euo pipefail
SRC=${1:-"../eleanor/orchestrator"}
DST=$(cd "$(dirname "$0")/.." && pwd)/src/orchestrator

if [ ! -d "$SRC" ]; then
  echo "Source dir $SRC not found" >&2
  exit 1
fi

rsync -av --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$SRC"/ "$DST"/

echo "Synced orchestrator code from $SRC to $DST"
