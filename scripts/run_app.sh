#!/usr/bin/env bash
# Launch the Sub-Centre Mind Streamlit demo (local only).
#
# Defaults assume Ollama is already running (start with `ollama serve` if not)
# and `gemma4:latest` is pulled. Run from repo root.
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${SCM_APP_PORT:-8501}"
ADDR="${SCM_APP_ADDR:-127.0.0.1}"

mkdir -p data/logs data/nudges

echo "Sub-Centre Mind app:"
echo "  http://${ADDR}:${PORT}"
echo "  audit log:    ${SCM_AUDIT_LOG:-data/logs/sample_events.jsonl}"
echo "  nudge store:  ${SCM_NUDGE_STORE:-data/nudges/store.json}"
echo

exec streamlit run app/streamlit_app.py \
  --server.address="${ADDR}" \
  --server.port="${PORT}" \
  --server.headless=true \
  --browser.gatherUsageStats=false
