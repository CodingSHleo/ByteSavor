"""
L1 Hard Evaluator — 纯代码规则检查 Agent 输出，不调用 LLM。
检查：推荐非空、核心食材覆盖、低置信识别、工具错误、需用户确认的软性判断。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.agent.state import AgentState
from app.services.food_synonyms import normalize_ingredient_name

Verdict = Literal["PASS", "PARTIAL", "FAIL", "CONFLICT"]


@dataclass
class EvaluationResult:
    verdict: Verdict
    issues: list[dict] = field(default_factory=list)   # [{code, message, tool?}]
    suggestions: list[str] = field(default_factory=list)


def evaluate_hard(state: AgentState) -> EvaluationResult:
    """对当前 AgentState 执行硬规则评估。"""
    verdict: Verdict = "PASS"
    issues: list[dict] = []
    suggestions: list[str] = []

    completed = set(state.get("completed_tools", []))
    errors = state.get("errors", [])
    recipes = state.get("recipes", [])
    # P1-7: 核心食材优先用 intent.ingredients（用户明确输入），不用全部 state["ingredients"]
    core_ingredients = state["intent"].get("ingredients") or []
    sense_result = state.get("sense_result") or {}

    # ── 1. decision 结果为空 → FAIL ──
    if "decision" in completed and not recipes:
        issues.append({
            "code": "NO_RECIPE",
            "message": "推荐工具执行完成但未返回任何菜谱",
            "tool": "decision",
        })
        suggestions.append("检查食材识别结果或放松筛选条件")
        verdict = _worse(verdict, "FAIL")

    # ── 2. 核心食材覆盖率 < 50% → CONFLICT；完全不使用 → FAIL ──
    # P1-7: 只对用户明确输入的核心食材（intent.ingredients）做硬约束
    if recipes and core_ingredients:
        used = _count_core_ingredient_coverage(recipes, core_ingredients)
        total = len(core_ingredients)
        if used == 0:
            issues.append({
                "code": "CORE_INGREDIENT_MISSED",
                "message": f"推荐菜谱未使用任何用户输入食材（{', '.join(core_ingredients[:5])}），覆盖率 0/{total}",
                "tool": "decision",
            })
            suggestions.append("扩大食材匹配或向用户解释无匹配原因")
            verdict = _worse(verdict, "FAIL")
        elif used < total * 0.5:
            issues.append({
                "code": "CORE_INGREDIENT_MISSED",
                "message": f"核心食材覆盖率 {used}/{total}，低于 50%",
                "tool": "decision",
            })
            suggestions.append(f"优先推荐包含 {', '.join(core_ingredients[:5])} 的菜谱")
            verdict = _worse(verdict, "CONFLICT")

    # ── 3. sense 识别结果存在低置信度（confidence < 0.5）→ PARTIAL ──
    if "sense" in completed and sense_result:
        sense_ings = sense_result.get("ingredients", [])
        low_conf = [i for i in sense_ings if isinstance(i, dict) and i.get("confidence", 0) < 0.5]
        if low_conf:
            names = [i.get("name", "?") for i in low_conf[:5]]
            issues.append({
                "code": "LOW_CONFIDENCE_INGREDIENT",
                "message": f"以下食材识别置信度低: {', '.join(names)}",
                "tool": "sense",
            })
            suggestions.append("请在界面上标记为'待确认'，让用户核实后确认")
            verdict = _worse(verdict, "PARTIAL")

    # ── 4. 工具异常 → FAIL ──
    for err in errors:
        code = err.get("error_code", "UNKNOWN")
        if code == "MAX_STEPS":
            continue  # MAX_STEPS 单独由 termination_reason 处理
        issues.append({
            "code": "TOOL_ERROR",
            "message": f"工具 [{err.get('tool', 'unknown')}] 错误: {err.get('message', '')}",
            "tool": err.get("tool"),
        })
        suggestions.append("检查外部服务状态或重试")
        verdict = _worse(verdict, "FAIL")

    # ── 5. 硬规则无法判断的软性问题 → NEEDS_USER_CONFIRMATION ──
    # P1-6: 不把 PASS 降为 PARTIAL，正常推荐仍保持 PASS
    if recipes and verdict == "PASS":
        issues.append({
            "code": "NEEDS_USER_CONFIRMATION",
            "message": "菜谱是否符合您的口味？是否接受推荐菜谱使用的替代食材？",
            "tool": "decision",
        })
        suggestions.append("请用户确认口味偏好和食材替代方案")

    return EvaluationResult(verdict=verdict, issues=issues, suggestions=suggestions)


def _count_core_ingredient_coverage(recipes: list[dict], core_ingredients: list[str]) -> int:
    """统计核心食材中被至少一个菜谱覆盖的数量。
    P1-8: 使用同义词标准化，确保番茄↔西红柿、土豆↔马铃薯等匹配。
    """
    covered = set()
    for r in recipes:
        ri = [normalize_ingredient_name(ing.get("name", "")) for ing in (r.get("ingredients", []) or [])]
        title = normalize_ingredient_name(r.get("title", ""))
        search_text = " ".join(ri) + " " + title
        for ci in core_ingredients:
            norm_ci = normalize_ingredient_name(ci)
            if norm_ci in search_text:
                covered.add(ci)
    return len(covered)


_PRIORITY: dict[str, int] = {"PASS": 0, "PARTIAL": 1, "CONFLICT": 2, "FAIL": 3}


def _worse(current: Verdict, candidate: Verdict) -> Verdict:
    return candidate if _PRIORITY.get(candidate, 0) > _PRIORITY.get(current, 0) else current
