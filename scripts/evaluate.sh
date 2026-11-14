#!/usr/bin/env bash
# Run the judged query set with keyword-only and hybrid search. Writes eval/RESULTS.md.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
need ELASTICSEARCH_URL ELASTIC_API_KEY
exec python3 "$ROOT/eval/run_eval.py"
