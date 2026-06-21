"""测试 L1 Hard Evaluator：PASS / PARTIAL / FAIL / CONFLICT 四种 verdict。"""
import pytest
from app.agent.evaluator import evaluate_hard
from app.agent.state import new_agent_state


def test_evaluator_pass_empty_state():
    """空状态（无工具完成）应为 PASS。"""
    state = new_agent_state("牛肉南瓜减脂30分钟", "conv1")
    result = evaluate_hard(state)
    assert result.verdict == "PASS"
    assert len(result.issues) == 0


def test_evaluator_fail_no_recipe():
    """decision 完成但无推荐 → FAIL + NO_RECIPE。"""
    state = new_agent_state("牛肉南瓜减脂30分钟", "conv2")
    state["completed_tools"] = ["decision"]
    state["recipes"] = []
    result = evaluate_hard(state)
    assert result.verdict == "FAIL"
    assert result.issues[0]["code"] == "NO_RECIPE"


def test_evaluator_conflict_core_ingredient_below_50pct():
    """3 个核心食材只覆盖 1 个 → CONFLICT。"""
    state = new_agent_state("牛肉南瓜鸡蛋减脂30分钟", "conv3")
    state["ingredients"] = ["牛肉", "南瓜", "鸡蛋"]
    state["recipes"] = [
        {"title": "牛肉面", "ingredients": [{"name": "牛肉"}, {"name": "面条"}]},
    ]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    assert result.verdict == "CONFLICT"
    assert result.issues[0]["code"] == "CORE_INGREDIENT_MISSED"


def test_evaluator_fail_zero_coverage():
    """推荐完全不使用输入食材 → FAIL。"""
    state = new_agent_state("牛肉南瓜减脂30分钟", "conv4")
    state["ingredients"] = ["牛肉", "南瓜"]
    state["recipes"] = [
        {"title": "番茄炒蛋", "ingredients": [{"name": "番茄"}, {"name": "鸡蛋"}]},
    ]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    assert result.verdict == "FAIL"
    assert result.issues[0]["code"] == "CORE_INGREDIENT_MISSED"


def test_evaluator_pass_full_coverage():
    """2 个核心食材全部覆盖 → PASS。"""
    state = new_agent_state("牛肉南瓜减脂30分钟", "conv5")
    state["ingredients"] = ["牛肉", "南瓜"]
    state["recipes"] = [
        {"title": "南瓜牛肉饭", "ingredients": [{"name": "牛肉"}, {"name": "南瓜"}]},
    ]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    assert result.verdict == "PASS"  # P1-6: 正常覆盖保持 PASS
    assert result.verdict not in ("FAIL", "CONFLICT", "PARTIAL")
    # 至少 50% 覆盖（2/2 = 100%）
    codes = [i["code"] for i in result.issues]
    assert "CORE_INGREDIENT_MISSED" not in codes


def test_evaluator_partial_low_confidence():
    """sense 结果有 confidence < 0.5 → PARTIAL。"""
    state = new_agent_state("识别食材", "conv6")
    state["completed_tools"] = ["sense"]
    state["sense_result"] = {
        "ingredients": [
            {"name": "苹果", "confidence": 0.95},
            {"name": "不明食材", "confidence": 0.3},
        ]
    }
    result = evaluate_hard(state)
    assert result.verdict == "PARTIAL"
    assert result.issues[0]["code"] == "LOW_CONFIDENCE_INGREDIENT"


def test_evaluator_fail_tool_error():
    """有工具错误（非 MAX_STEPS）→ FAIL。"""
    state = new_agent_state("测试", "conv7")
    state["errors"] = [
        {"tool": "sense", "error_code": "VLM_UNAVAILABLE", "message": "连接超时"},
    ]
    result = evaluate_hard(state)
    assert result.verdict == "FAIL"
    codes = [i["code"] for i in result.issues]
    assert "TOOL_ERROR" in codes


def test_evaluator_needs_user_confirmation():
    """有推荐结果且无硬错误 → 标记 NEEDS_USER_CONFIRMATION，但不降 verdict。"""
    state = new_agent_state("推荐一道菜", "conv8")
    state["recipes"] = [{"title": "番茄炒蛋", "ingredients": [{"name": "番茄"}]}]
    state["completed_tools"] = ["decision"]
    result = evaluate_hard(state)
    codes = [i["code"] for i in result.issues]
    assert "NEEDS_USER_CONFIRMATION" in codes
    assert result.verdict == "PASS"  # P1-6: 正常推荐不降级
