#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:8000}"
RUN_DB="${RUN_DB:-0}"
RUN_API_EVAL="${RUN_API_EVAL:-0}"

echo "== ByteSavor fullstack test bundle =="
echo "ROOT=$ROOT"
echo "API_BASE=$API_BASE"
echo "RUN_DB=$RUN_DB"
echo "RUN_API_EVAL=$RUN_API_EVAL"

echo
echo "== 1. Backend core + Eval mock + H5 build =="
"$ROOT/scripts/verify_quick.sh"

echo
echo "== 2. Frontend static regressions =="
node "$ROOT/scripts/verify_frontend_regressions.mjs"

if [[ "$RUN_DB" == "1" ]]; then
  echo
  echo "== 3. DB integration tests =="
  "$ROOT/scripts/verify_db.sh"
else
  echo
  echo "== 3. DB integration tests skipped =="
  echo "Set RUN_DB=1 when MySQL/Redis and .env are ready."
fi

if [[ "$RUN_API_EVAL" == "1" ]]; then
  echo
  echo "== 4. Eval API mode =="
  API_BASE="$API_BASE" "$ROOT/scripts/verify_eval_api.sh"
else
  echo
  echo "== 4. Eval API mode skipped =="
  echo "Start backend and set RUN_API_EVAL=1 to verify real HTTP Agent flow."
fi

echo
echo "== fullstack test bundle completed =="
