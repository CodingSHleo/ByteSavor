"""测试推荐一致性：核心食材覆盖、推荐理由码、memory 匹配。"""
import pytest
from app.services.decision import REASON_TEMPLATES
from app.agent.evaluator import evaluate_hard, _count_core_ingredient_coverage
from app.agent.state import new_agent_state


def test_reason_templates_have_memory_codes():
    """推荐理由模板应包含 MEMORY_MATCH 和 INVENTORY_MATCH。"""
    assert "MEMORY_MATCH" in REASON_TEMPLATES, "Missing MEMORY_MATCH reason code"
    assert "INVENTORY_MATCH" in REASON_TEMPLATES, "Missing INVENTORY_MATCH reason code"
    assert "PREF_MATCH" in REASON_TEMPLATES, "Missing PREF_MATCH reason code"


def test_core_ingredient_coverage_full_match():
    """全部核心食材被覆盖 → 返回总数。"""
    recipes = [
        {"title": "牛肉南瓜饭", "ingredients": [{"name": "牛肉"}, {"name": "南瓜"}]},
    ]
    coverage = _count_core_ingredient_coverage(recipes, ["牛肉", "南瓜"])
    assert coverage == 2


def test_core_ingredient_coverage_partial():
    """仅覆盖部分核心食材。"""
    recipes = [
        {"title": "牛肉面", "ingredients": [{"name": "牛肉"}, {"name": "面条"}]},
    ]
    coverage = _count_core_ingredient_coverage(recipes, ["牛肉", "南瓜"])
    assert coverage == 1


def test_core_ingredient_coverage_none():
    """完全不覆盖核心食材。"""
    recipes = [
        {"title": "番茄炒蛋", "ingredients": [{"name": "番茄"}, {"name": "鸡蛋"}]},
    ]
    coverage = _count_core_ingredient_coverage(recipes, ["牛肉", "南瓜"])
    assert coverage == 0


def test_evaluator_50pct_rule_2_ingredients():
    """2 个核心食材至少覆盖 1 个（50%）。"""
    state = new_agent_state("牛肉南瓜减脂30分钟", "conv_test")
    state["ingredients"] = ["牛肉", "南瓜"]
    state["recipes"] = [
        {"title": "牛肉面", "ingredients": [{"name": "牛肉"}, {"name": "面条"}]},
    ]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    # 1/2 = 50%，不算低于 50%，应为 PASS 或 PARTIAL（用户确认触发）
    codes = [i["code"] for i in result.issues]
    assert "CORE_INGREDIENT_MISSED" not in codes, f"50% coverage should pass, got {codes}"


def test_evaluator_50pct_rule_3_ingredients():
    """3 个核心食材只覆盖 1 个（33%）→ CONFLICT。"""
    state = new_agent_state("牛肉南瓜鸡蛋减脂30分钟", "conv_test2")
    state["ingredients"] = ["牛肉", "南瓜", "鸡蛋"]
    state["recipes"] = [
        {"title": "牛肉面", "ingredients": [{"name": "牛肉"}, {"name": "面条"}]},
    ]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    assert result.verdict == "CONFLICT"
    assert result.issues[0]["code"] == "CORE_INGREDIENT_MISSED"


def test_evaluator_50pct_rule_3_ingredients_pass():
    """3 个核心食材覆盖 2 个（67%）→ 通过。"""
    state = new_agent_state("牛肉南瓜鸡蛋减脂30分钟", "conv_test3")
    state["ingredients"] = ["牛肉", "南瓜", "鸡蛋"]
    state["recipes"] = [
        {"title": "牛肉南瓜炒蛋", "ingredients": [{"name": "牛肉"}, {"name": "南瓜"}, {"name": "鸡蛋"}]},
    ]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    codes = [i["code"] for i in result.issues]
    assert "CORE_INGREDIENT_MISSED" not in codes, f"67% coverage should pass, got {codes}"
