"""确定性规则 scorer：不调用 LLM，只做结构化检查。"""
from __future__ import annotations


def score_result(case: dict, result: dict) -> dict:
    """对单条用例的 Agent 返回结果打分。
    返回 {case_id, total_score, max_score, failed_checks, passed_checks, details}
    """
    checks = case.get("expected_checks", {})
    failed = []
    passed = []
    details = {}

    for check_key, expected in checks.items():
        ok, detail = _check(result, check_key, expected)
        details[check_key] = detail
        if ok:
            passed.append(check_key)
        else:
            failed.append(check_key)

    # ── 默认失败规则：内部异常不放过 ──
    termination = result.get("termination_reason", "")
    eval_events = [e for e in result.get("events", []) if e.get("type") == "evaluation"]
    eval_verdict = eval_events[0].get("verdict", "") if eval_events else ""
    status = result.get("status", "")

    allow_failure = case.get("allow_failure", False)
    if not allow_failure:
        if termination == "TOOL_ERROR":
            failed.append("termination_reason_is_TOOL_ERROR")
            details["termination_reason_is_TOOL_ERROR"] = f"不应出现 TOOL_ERROR, termination_reason={termination}"
        else:
            passed.append("termination_reason_ok")
            details["termination_reason_ok"] = f"termination_reason={termination}"

        if eval_verdict == "FAIL":
            failed.append("evaluation_verdict_is_FAIL")
            details["evaluation_verdict_is_FAIL"] = f"不应出现 FAIL verdict, verdict={eval_verdict}"
        else:
            passed.append("evaluation_verdict_ok")
            details["evaluation_verdict_ok"] = f"verdict={eval_verdict}"

        if status == "degraded":
            failed.append("status_is_degraded")
            details["status_is_degraded"] = f"不应出现 degraded status, status={status}"
        else:
            passed.append("status_ok")
            details["status_ok"] = f"status={status}"

    total = len(passed)
    max_score = (len(checks) if checks else 1) + 3  # +3 for the default fail checks
    return {
        "case_id": case["case_id"],
        "name": case.get("name", ""),
        "total_score": total,
        "max_score": max_score,
        "score_pct": round(total / max_score * 100) if max_score else 0,
        "passed_checks": passed,
        "failed_checks": failed,
        "details": details,
    }


def _check(result: dict, key: str, expected) -> tuple[bool, str]:
    events = result.get("events", [])
    recipes = result.get("recipes", [])
    status = result.get("status", "")

    if key == "has_recipes":
        ok = "recipes" in result
        return ok, f"has_recipes={ok}"

    if key == "recipes_non_empty":
        ok = len(recipes) > 0
        return ok, f"recipes count={len(recipes)}"

    if key == "reply_not_empty":
        reply = result.get("reply", "")
        ok = bool(reply)
        return ok, f"reply len={len(reply)}"

    if key == "has_evaluation":
        eval_events = [e for e in events if e.get("type") == "evaluation"]
        ok = len(eval_events) > 0
        return ok, f"evaluation events count={len(eval_events)}"

    if key == "has_termination_reason":
        reason = result.get("termination_reason", "")
        ok = bool(reason)
        return ok, f"termination_reason={reason}"

    if key == "has_termination_reason_needs_input":
        reason = result.get("termination_reason", "")
        ok = reason == "NEEDS_INPUT"
        return ok, f"termination_reason={reason}"

    if key == "core_ingredient_coverage_min_1":
        return _check_ingredient_coverage(recipes, expected, min_count=1)

    if key == "core_ingredient_coverage_min_2":
        return _check_ingredient_coverage(recipes, expected, min_count=2)

    if key == "status":
        ok = status == expected
        return ok, f"status={status} expected={expected}"

    if key == "has_ask_user_event":
        ok = any(e.get("type") == "ask_user" for e in events)
        return ok, f"has_ask_user_event={ok}"

    if key == "has_phase_routing":
        ok = _has_phase(events, "ROUTING")
        return ok, f"has_phase_ROUTING={ok}"

    if key == "has_phase_executing":
        ok = _has_phase(events, "EXECUTING")
        return ok, f"has_phase_EXECUTING={ok}"

    if key == "has_phase_evaluating":
        ok = _has_phase(events, "EVALUATING")
        return ok, f"has_phase_EVALUATING={ok}"

    if key == "has_phase_finished":
        ok = _has_phase(events, "FINISHED")
        return ok, f"has_phase_FINISHED={ok}"

    if key == "events_non_empty":
        ok = len(events) > 0
        return ok, f"events count={len(events)}"

    return False, f"unknown check: {key}"


def _check_ingredient_coverage(recipes: list[dict], ingredients: list[str], min_count: int) -> tuple[bool, str]:
    if not ingredients:
        return True, "no ingredients to check"
    covered = 0
    for ing in ingredients:
        for r in recipes:
            title = r.get("title", "")
            ri = [i.get("name", "") for i in (r.get("ingredients", []) or [])]
            if ing in " ".join(ri) + " " + title:
                covered += 1
                break
    ok = covered >= min_count
    return ok, f"core ingredients covered: {covered}/{len(ingredients)}, need >= {min_count}"


def _has_phase(events: list[dict], phase: str) -> bool:
    return any(e.get("phase") == phase for e in events)
