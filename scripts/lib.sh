#!/usr/bin/env bash
# Shared helpers. Source this file; do not run it. Works with macOS bash 3.2.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$ROOT/.env" ]; then
  echo "Missing $ROOT/.env. Copy .env.example to .env and fill it in." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
. "$ROOT/.env"
set +a
KIBANA_URL="${KIBANA_URL%/}"
ELASTICSEARCH_URL="${ELASTICSEARCH_URL%/}"
INDEX_NAME="${INDEX_NAME:-albisgrat-knowledge}"

ok()   { printf '  \033[32mOK\033[0m    %s\n' "$*"; }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; }
note() { printf '  \033[33mNOTE\033[0m  %s\n' "$*"; }
say()  { printf '\n%s\n' "$*"; }

need() {
  local v missing=0
  for v in "$@"; do
    if [ -z "${!v:-}" ]; then echo "Missing $v in .env" >&2; missing=1; fi
  done
  [ "$missing" -eq 0 ] || exit 1
}
