#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/venv/bin/python"

export JWT_SECRET="${JWT_SECRET:-test-review-secret}"

echo "== ByteSavor quick verification =="
echo "ROOT=$ROOT"

echo
echo "== 1. Core non-DB tests =="
"$PY" -m pytest -q \
  "$ROOT/tests/test_agent_evaluator.py" \
  "$ROOT/tests/test_agent_memory_context.py" \
  "$ROOT/tests/test_agent_loop_engineering.py" \
  "$ROOT/tests/test_decision_memory_matching.py" \
  "$ROOT/tests/test_correction_memory.py" \
  "$ROOT/tests/test_agent_runtime.py" \
  "$ROOT/tests/test_langgraph_agent.py" \
  "$ROOT/tests/test_nutrition_calculator.py" \
  "$ROOT/tests/test_agent_memory_api.py" \
  "$ROOT/tests/test_agent_confirmation_prompts.py" \
  "$ROOT/tests/test_agent.py" \
  "$ROOT/tests/test_food_guide.py"

echo
echo "== 2. Eval mock =="
"$PY" "$ROOT/evals/runner.py" --quick --mode mock

echo
echo "== 3. H5 build =="
(
  cd "$ROOT/bsapp"
  npm run build:h5
)

echo
echo "== quick verification passed =="
