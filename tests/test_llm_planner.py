import pytest

from app.agent.llm_planner import choose_action_with_llm
from app.agent.planner import build_candidate_actions
from app.agent.runtime import AgentRuntime
from app.agent.tools import ToolRegistry


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_llm_selecting_unknown_tool_falls_back_to_rule_planner(monkeypatch):
    tools = ToolRegistry()
    calls = []

    async def decision(_state):
        calls.append("decision")
        return {"recipes": [{"recipe_id": "db_1", "title": "牛肉韭黄"}]}

    async def task(_state):
        calls.append("task")
        return {"shopping_list": [{"name": "韭黄"}]}

    tools.register("decision", decision)
    tools.register("task", task)
    monkeypatch.setattr("app.agent.llm_planner.settings.agent_llm_planner_enabled", True)
    async def fake_choose(_state, _candidates):
        return {"kind": "tool", "tool": "admin_delete", "reason": "越权"}

    monkeypatch.setattr("app.agent.llm_planner.choose_action_with_llm", fake_choose)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run("牛肉韭黄推荐一道菜", "conv_llm_bad_tool")

    assert calls == ["decision"]
    plan = next(event for event in result["events"] if event["type"] == "plan")
    assert plan["planner_source"] == "rule_fallback"
    assert plan["tool"] == "decision"


async def test_llm_can_only_select_candidate_tool(monkeypatch):
    tools = ToolRegistry()
    calls = []

    async def decision(_state):
        calls.append("decision")
        return {"recipes": [{"recipe_id": "db_2", "title": "韭黄炒蛋"}]}

    tools.register("decision", decision)
    monkeypatch.setattr("app.agent.llm_planner.settings.agent_llm_planner_enabled", True)
    monkeypatch.setattr("app.agent.llm_planner.settings.llm_api_key", "sk-test")
    monkeypatch.setattr("app.agent.llm_planner.settings.llm_api_url", "https://llm.invalid/v1/chat/completions")
    async def fake_choose(_state, _candidates):
        return {"kind": "tool", "tool": "decision", "reason": "候选中最匹配"}

    monkeypatch.setattr("app.agent.llm_planner.choose_action_with_llm", fake_choose)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run("推荐一道韭黄炒蛋", "conv_llm_candidate")

    assert calls == ["decision"]
    assert result["recipes"][0]["recipe_id"] == "db_2"
    plan = next(event for event in result["events"] if event["type"] == "plan")
    assert plan["planner_source"] == "llm"
    assert plan["candidate_tools"] == ["decision"]
    assert plan["llm_reason"] == "候选中最匹配"


async def test_no_api_key_does_not_call_network(monkeypatch):
    from app.agent.state import new_agent_state

    called = False

    class FailingClient:
        def __init__(self, *args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network should not be called")

    monkeypatch.setattr("app.agent.llm_planner.settings.agent_llm_planner_enabled", True)
    monkeypatch.setattr("app.agent.llm_planner.settings.llm_api_key", "")
    monkeypatch.setattr("app.agent.llm_planner.settings.llm_api_url", "https://llm.invalid/v1/chat/completions")
    monkeypatch.setattr("app.agent.llm_planner.httpx.AsyncClient", FailingClient)

    state = new_agent_state("推荐一道菜", "conv_no_key")
    result = await choose_action_with_llm(state, [{"kind": "tool", "tool": "decision"}])

    assert result is None
    assert called is False


async def test_candidate_tools_come_from_registry_descriptors():
    from app.agent.state import new_agent_state

    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": []}

    tools.register("decision", decision)
    state = new_agent_state("推荐一道菜", "conv_candidates")

    candidates = build_candidate_actions(state, tools.describe())

    assert [candidate["tool"] for candidate in candidates] == ["decision"]
    assert candidates[0]["category"] == "decision"
    assert candidates[0]["requires_image"] is False


async def test_candidate_filter_respects_required_recipe_input():
    from app.agent.state import new_agent_state

    tools = ToolRegistry()

    async def task(_state):
        return {"shopping_list": []}

    tools.register("task", task)
    state = new_agent_state("帮我生成购物清单", "conv_task_without_recipes")

    assert build_candidate_actions(state, tools.describe()) == []

    state["recipes"] = [{"recipe_id": "db_1", "title": "数据库菜谱"}]
    candidates = build_candidate_actions(state, tools.describe())

    assert [candidate["tool"] for candidate in candidates] == ["task"]


async def test_planner_cannot_invent_recipe_id(monkeypatch):
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": [{"recipe_id": "db_only", "title": "数据库菜谱"}]}

    tools.register("decision", decision)
    monkeypatch.setattr("app.agent.llm_planner.settings.agent_llm_planner_enabled", True)
    async def fake_choose(_state, _candidates):
        return {"kind": "tool", "tool": "decision", "reason": "recipe_id=made_up"}

    monkeypatch.setattr("app.agent.llm_planner.choose_action_with_llm", fake_choose)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run("推荐一道菜，LLM 不得编造菜谱", "conv_no_recipe_forge")

    assert [recipe["recipe_id"] for recipe in result["recipes"]] == ["db_only"]


async def test_image_identify_recommend_candidates_force_sense_before_decision(monkeypatch):
    from app.agent.state import new_agent_state

    tools = ToolRegistry()

    async def sense(_state):
        return {"ingredients": [{"name": "番茄"}]}

    async def decision(_state):
        return {"recipes": []}

    tools.register("sense", sense)
    tools.register("decision", decision)
    state = new_agent_state(
        "识别图片里的食材并推荐菜谱",
        "conv_image_first_candidates",
        image_url="https://example.test/food.jpg",
    )

    candidates = build_candidate_actions(state, tools.describe())

    assert [candidate["tool"] for candidate in candidates] == ["sense"]


async def test_llm_cannot_skip_required_sense_for_image_recommendation(monkeypatch):
    tools = ToolRegistry()
    calls = []

    async def sense(_state):
        calls.append("sense")
        return {"ingredients": [{"name": "番茄"}]}

    async def decision(_state):
        calls.append("decision")
        return {"recipes": [{"recipe_id": "db_after_sense", "title": "番茄炒蛋"}]}

    tools.register("sense", sense)
    tools.register("decision", decision)
    monkeypatch.setattr("app.agent.llm_planner.settings.agent_llm_planner_enabled", True)

    async def fake_choose(_state, _candidates):
        return {"kind": "tool", "tool": "decision", "reason": "试图跳过 sense"}

    monkeypatch.setattr("app.agent.llm_planner.choose_action_with_llm", fake_choose)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run(
        "识别图片里的食材并推荐菜谱",
        "conv_llm_no_skip_sense",
        image_url="https://example.test/food.jpg",
    )

    assert calls == ["sense", "decision"]
    plan_events = [event for event in result["events"] if event["type"] == "plan"]
    assert plan_events[0]["tool"] == "sense"
    assert plan_events[0]["candidate_tools"] == ["sense"]
    assert plan_events[0]["planner_source"] == "rule_fallback"


async def test_new_explicit_ingredients_force_fresh_decision_in_same_conversation():
    from app.agent.langgraph_runtime import LangGraphAgent

    tools = ToolRegistry()
    calls = []

    async def decision(state):
        calls.append(list(state["ingredients"]))
        if "番茄" in state["ingredients"]:
            return {"recipes": [{
                "recipe_id": "r_tomato_beef",
                "title": "番茄牛肉",
                "match_score": 0.95,
                "ingredients": [{"name": "番茄"}, {"name": "牛肉"}],
            }]}
        return {"recipes": [{
            "recipe_id": "r_pepper_beef",
            "title": "青椒牛肉",
            "match_score": 0.8,
            "ingredients": [{"name": "青椒"}, {"name": "牛肉"}],
        }]}

    tools.register("decision", decision)
    runtime = LangGraphAgent(tools=tools)

    first = await runtime.run("青椒牛肉减脂30分钟", "conv_new_food_refresh")
    second = await runtime.run("番茄牛肉减脂30分钟", "conv_new_food_refresh")

    assert first["recipes"][0]["recipe_id"] == "r_pepper_beef"
    assert second["recipes"][0]["recipe_id"] == "r_tomato_beef"
    assert calls == [["牛肉", "青椒"], ["牛肉", "番茄"]]
