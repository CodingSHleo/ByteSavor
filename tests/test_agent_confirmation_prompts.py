"""V3-6: confirmation_prompts 按 issue code 独立生成测试。"""
from app.routers.agent import _build_confirmation_prompts


def make_evaluation_event(issues):
    return {
        "type": "evaluation",
        "verdict": "CONFLICT",
        "issues": issues,
    }


def test_confirmation_core_ingredient_missed_alone():
    """只有 CORE_INGREDIENT_MISSED → 应生成 SUBSTITUTE_CONFIRM。"""
    result = {
        "events": [make_evaluation_event([
            {"code": "CORE_INGREDIENT_MISSED", "message": "覆盖率 1/3 低于 50%", "tool": "decision"}
        ])],
        "recipes": [{"title": "测试菜"}],
    }
    prompts = _build_confirmation_prompts(result)
    codes = [p["code"] for p in prompts]
    assert "SUBSTITUTE_CONFIRM" in codes, f"应有 SUBSTITUTE_CONFIRM, 实际: {codes}"
    assert "TASTE_CONFIRM" in codes, f"有 recipes 应也有 TASTE_CONFIRM, 实际: {codes}"


def test_confirmation_low_confidence_alone():
    """只有 LOW_CONFIDENCE_INGREDIENT → 应生成 INGREDIENT_CONFIRM。"""
    result = {
        "events": [make_evaluation_event([
            {"code": "LOW_CONFIDENCE_INGREDIENT", "message": "苹果置信度 0.3", "tool": "sense"}
        ])],
    }
    prompts = _build_confirmation_prompts(result)
    codes = [p["code"] for p in prompts]
    assert "INGREDIENT_CONFIRM" in codes, f"应有 INGREDIENT_CONFIRM, 实际: {codes}"


def test_confirmation_no_duplicate_prompts():
    """多个 evaluation event 不应生成重复 prompt。"""
    result = {
        "events": [
            make_evaluation_event([
                {"code": "CORE_INGREDIENT_MISSED", "message": "覆盖率 1/3", "tool": "decision"}
            ]),
            make_evaluation_event([
                {"code": "CORE_INGREDIENT_MISSED", "message": "覆盖率 0/2", "tool": "decision"}
            ]),
        ],
        "recipes": [{"title": "测试菜"}],
    }
    prompts = _build_confirmation_prompts(result)
    sub_count = sum(1 for p in prompts if p["code"] == "SUBSTITUTE_CONFIRM")
    assert sub_count == 1, f"SUBSTITUTE_CONFIRM 不应重复, 实际 {sub_count} 个"


def test_confirmation_no_evaluation_no_prompts():
    """无 evaluation event → 空 prompts（除非有 recipes）。"""
    result = {"events": []}
    prompts = _build_confirmation_prompts(result)
    assert prompts == []


def test_confirmation_recipes_triggers_taste():
    """有 recipes 无 evaluation → 也应生成 TASTE_CONFIRM。"""
    result = {
        "events": [],
        "recipes": [{"title": "测试菜"}],
    }
    prompts = _build_confirmation_prompts(result)
    codes = [p["code"] for p in prompts]
    assert "TASTE_CONFIRM" in codes, f"有 recipes 应有 TASTE_CONFIRM, 实际: {codes}"
