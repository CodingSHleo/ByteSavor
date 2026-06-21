#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/venv/bin/python"
API_BASE="${API_BASE:-http://127.0.0.1:8000}"

export JWT_SECRET="${JWT_SECRET:-test-review-secret}"

echo "== ByteSavor Eval API verification =="
echo "API_BASE=$API_BASE"

echo
echo "== 1. Check API health by calling /v1/agent/execute =="
probe="$(
  curl -s -X POST "$API_BASE/v1/agent/execute" \
    -H 'Content-Type: application/json' \
    -d '{"input":"牛肉南瓜减脂30分钟","conversation_id":"eval_api_probe"}'
)"

echo "$probe" | "$PY" -c '
import json, sys
body = json.load(sys.stdin)
data = body.get("data", body)
events = data.get("events", [])
if not events:
    raise SystemExit("API probe failed: no events returned")
if not any(e.get("phase") for e in events):
    raise SystemExit("API probe failed: events have no phase; backend may be old")
if "termination_reason" not in data:
    raise SystemExit("API probe failed: missing termination_reason; backend may be old")
print("API probe passed")
'

echo
echo "== 2. Run Eval API mode =="
"$PY" "$ROOT/evals/runner.py" --quick --mode api --api-base "$API_BASE" --prefix latest-api

echo
echo "== Eval API verification passed =="
