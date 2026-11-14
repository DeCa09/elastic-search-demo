#!/usr/bin/env bash
# Build everything: index, documents, role and users, Agent Builder agent.
# Usage: scripts/setup.sh [all|index|ingest|security|agent|status|delete]
set -euo pipefail
. "$(dirname "$0")/lib.sh"
need KIBANA_URL ELASTICSEARCH_URL ELASTIC_API_KEY
exec python3 "$ROOT/elastic/setup_search.py" "${1:-all}"
