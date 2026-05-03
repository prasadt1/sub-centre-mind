#!/usr/bin/env bash
# Start the Ollama-compatible dev shim on port 18765 (for SCM_BACKEND=cactus).
# Requires: ollama serve (or reachable --upstream) separately.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/cactus_bridge_shim.py \
  --host "${SCM_SHIM_HOST:-127.0.0.1}" \
  --port "${SCM_SHIM_PORT:-18765}" \
  --upstream "${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
