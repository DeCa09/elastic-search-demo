#!/usr/bin/env bash
# Run a demo query from the terminal.
# Usage: scripts/ask.sh keyword|hybrid "question" [--as compliance_officer|relationship_manager] [--current]
set -euo pipefail
. "$(dirname "$0")/lib.sh"
need ELASTICSEARCH_URL ELASTIC_API_KEY
exec python3 "$ROOT/elastic/queries.py" "$@"
