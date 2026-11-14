#!/usr/bin/env bash
# Check that everything is ready for the demo. Exit code 0 means go.
# Run it 30 minutes before, and again 5 minutes before.
set -uo pipefail
. "$(dirname "$0")/lib.sh"
need KIBANA_URL ELASTICSEARCH_URL ELASTIC_API_KEY COMPLIANCE_OFFICER_PASSWORD RELATIONSHIP_MANAGER_PASSWORD
fails=0

say "1. Index, embedding model, users, agent"
python3 "$ROOT/elastic/setup_search.py" status || fails=$((fails + 1))

say "2. The demo queries"
Q="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["cross_language_question"])' "$ROOT/demo/demo_queries.json")"
TARGET="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["cross_language_target_title"])' "$ROOT/demo/demo_queries.json")"
kw="$(python3 "$ROOT/elastic/queries.py" keyword "$Q" --as relationship_manager)"
hy="$(python3 "$ROOT/elastic/queries.py" hybrid "$Q" --as relationship_manager)"
if echo "$kw" | grep -q "$TARGET"; then bad "keyword search already finds the target (moment 1 would not work)"; fails=$((fails + 1)); else ok "keyword search does not find '$TARGET'"; fi
if echo "$hy" | grep -q "$TARGET"; then ok "hybrid search finds '$TARGET' in the top 5"; else bad "hybrid search does not find '$TARGET' in the top 5"; fails=$((fails + 1)); fi
RQ="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["permission_question"])' "$ROOT/demo/demo_queries.json")"
co="$(python3 "$ROOT/elastic/queries.py" hybrid "$RQ" --as compliance_officer --size 8)"
rm="$(python3 "$ROOT/elastic/queries.py" hybrid "$RQ" --as relationship_manager --size 8)"
if echo "$co" | grep -q "RESTRICTED"; then ok "compliance_officer sees a restricted document"; else bad "compliance_officer does not see the restricted memo"; fails=$((fails + 1)); fi
if echo "$rm" | grep -q "RESTRICTED"; then bad "relationship_manager sees a restricted document"; fails=$((fails + 1)); else ok "relationship_manager sees no restricted document"; fi

say "3. Check by hand (not scriptable)"
note "Agent chat answers the warm-up question with citations (RUNBOOK.md)"
note "Two browser windows are logged in: compliance_officer and relationship_manager"
note "Backup video and screenshots are open in another window (FALLBACK.md)"

echo
if [ "$fails" -eq 0 ]; then
  printf '\033[32mPREFLIGHT PASSED\033[0m  You are ready.\n'
else
  printf '\033[31mPREFLIGHT FAILED\033[0m  %s check(s) failed. See FALLBACK.md if you are short on time.\n' "$fails"
  exit 1
fi
