#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/venv/bin/python"

export JWT_SECRET="${JWT_SECRET:-test-review-secret}"

echo "== ByteSavor DB verification =="
echo "This requires local MySQL/Redis access."
echo "If this fails with Operation not permitted on 127.0.0.1:3306, rerun in an environment allowed to access local MySQL."

"$PY" -m pytest -q \
  "$ROOT/tests/test_auth.py" \
  "$ROOT/tests/test_decision.py" \
  "$ROOT/tests/test_meals_inventory.py" \
  "$ROOT/tests/test_feedback_memory.py" \
  "$ROOT/tests/test_inventory_stats.py" \
  "$ROOT/tests/test_recipe_checker.py" \
  "$ROOT/tests/test_favorites.py" \
  "$ROOT/tests/test_community.py" \
  "$ROOT/tests/test_community_recipe_flow.py" \
  "$ROOT/tests/test_agent_tools_inventory_favorites.py"

echo
echo "== DB verification passed =="
