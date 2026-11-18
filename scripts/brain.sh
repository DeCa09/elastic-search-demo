#!/usr/bin/env bash
# The company-brain demo (second demo, on an Elasticsearch Serverless project).
# Usage: scripts/brain.sh all|sources|ai-index|agents|workflow|status|delete
#        scripts/brain.sh compare [question-id ...] [--only-brain]
set -euo pipefail
. "$(dirname "$0")/lib.sh"
need BRAIN_ELASTICSEARCH_URL BRAIN_KIBANA_URL BRAIN_API_KEY
if [ "${1:-all}" = "compare" ]; then
  shift
  exec python3 "$ROOT/brain/compare.py" "$@"
fi
exec python3 "$ROOT/brain/setup_brain.py" "${1:-all}"
