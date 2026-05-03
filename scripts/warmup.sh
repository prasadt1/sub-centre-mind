#!/usr/bin/env bash
# Warm Ollama so the next request doesn't pay the model-load cost.
#
# Usage:
#   bash scripts/warmup.sh                  # default model gemma4:latest
#   MODEL=gemma4:latest bash scripts/warmup.sh
set -euo pipefail

MODEL="${MODEL:-${SCM_MODEL:-gemma4:latest}}"
URL="${OLLAMA_GENERATE_URL:-http://localhost:11434/api/generate}"

echo "Warming ${MODEL} via ${URL} ..."
START=$(date +%s)

curl -sS "$URL" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"prompt\":\"warm up\",\"think\":false,\"stream\":false,\"options\":{\"num_predict\":4}}" \
  > /dev/null

END=$(date +%s)
echo "Warm-up done in $((END - START))s. First real query should now be fast."
