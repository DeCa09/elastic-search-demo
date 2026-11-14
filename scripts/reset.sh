#!/usr/bin/env bash
# Delete the index and build it again from the files in data/. Target: under 5 minutes.
# Users, role and agent are recreated too, so one command gives a clean demo.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
need KIBANA_URL ELASTICSEARCH_URL ELASTIC_API_KEY COMPLIANCE_OFFICER_PASSWORD RELATIONSHIP_MANAGER_PASSWORD
start="$(date +%s)"
say "Reset started $(date +%H:%M:%S)"
python3 "$ROOT/elastic/setup_search.py" all
total=$(( $(date +%s) - start ))
echo
if [ "$total" -le 300 ]; then
  printf '\033[32mRESET DONE\033[0m in %ss.\n' "$total"
else
  printf '\033[33mRESET DONE\033[0m in %ss (target is 300s).\n' "$total"
fi
note "Old Agent Builder conversations stay. Start a new chat for the next run."
