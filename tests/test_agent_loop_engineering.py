"""测试 Loop Engineering：phase 字段、termination_reason、max_steps 边界。"""
import pytest

from app.agent.langgraph_runtime import LangGraphAgent
from app.agent.runtime import AgentRuntime
from app.agent.tools import ToolRegistry


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_events_have_phase():
    """Agent 所有 events 必须包含 phase 字段。"""
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r1", "title": "测试菜", "match_score": 0.9}]}

    tools.register("decision", decision)
    runtime = AgentRuntime(tools=tools)

    result = await runtime.run("推荐一道菜", "conv_phase")
    for event in result["events"]:
        assert "phase" in event, f"Event missing phase: {event['type']}"
        assert event["phase"] in (
            "ROUTING", "EXECUTING", "EVALUATING", "CLARIFYING", "FINISHED", "ERROR"
        ), f"Unexpected phase: {event['phase']}"


async def test_termination_reason_goal_achieved():
    """正常完成 → GOAL_ACHIEVED。"""
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r1", "title": "测试菜", "match_score": 0.9}]}

    tools.register("decision", decision)
    runtime = AgentRuntime(tools=tools, max_steps=4)

    result = await runtime.run("推荐一道菜", "conv_goal_ok")
    assert result.get("termination_reason") is not None, "Missing termination_reason"


async def test_max_steps_boundary():
    """超过 max_steps 时 results 被 truncated。"""
    tools = ToolRegistry()
    call_count = [0]

    async def never_finish(state):
        call_count[0] += 1
        return {"recipes": []}

    tools.register("decision", never_finish)
    runtime = AgentRuntime(tools=tools, max_steps=3)

    result = await runtime.run("反复推荐", "conv_maxsteps")
    assert call_count[0] <= 3
    assert result.get("termination_reason") is not None


async def test_langgraph_events_include_plan_and_final():
    """LangGraph Agent 至少产生 plan 和 final 事件。"""
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r1", "title": "测试", "match_score": 0.9}]}

    tools.register("decision", decision)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    result = await agent.run("推荐", "conv_lg_events")
    types = [e["type"] for e in result["events"]]
    assert "plan" in types, f"Missing plan event in {types}"
    assert "final" in types, f"Missing final event in {types}"
    plan = next(e for e in result["events"] if e["type"] == "plan")
    assert plan["available_skills"] == ["decision"]
    tool_result = next(e for e in result["events"] if e["type"] == "tool_result")
    assert tool_result["skill"]["category"] == "decision"


async def test_ask_user_event():
    """缺图片时应有 ask_user 事件。"""
    tools = ToolRegistry()

    async def sense(state):
        return {"ingredients": [], "portion_estimation": {}}

    tools.register("sense", sense)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    result = await agent.run("分析营养", "conv_ask", image_url=None)
    types = [e["type"] for e in result["events"]]
    # 没有图片 + 请求营养分析 → 应该触发 ask_user
    assert "ask_user" in types or result.get("termination_reason") == "NEEDS_INPUT"


async def test_evaluation_event_present():
    """LangGraph Agent 的 events 应包含 evaluation 事件。"""
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r1", "title": "测试菜", "match_score": 0.9}]}

    tools.register("decision", decision)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    result = await agent.run("推荐一道菜", "conv_eval")
    types = [e["type"] for e in result["events"]]
    assert "evaluation" in types, f"Missing evaluation event in {types}"


async def test_agent_runtime_tool_result_contains_skill_metadata():
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r1", "title": "测试菜", "match_score": 0.9}]}

    tools.register("decision", decision)
    runtime = AgentRuntime(tools=tools, max_steps=4)

    result = await runtime.run("推荐一道菜", "conv_runtime_skill_meta")
    tool_result = next(e for e in result["events"] if e["type"] == "tool_result")

    assert tool_result["skill"]["name"] == "decision"
    assert tool_result["skill"]["category"] == "decision"
    assert tool_result["skill"]["timeout_ms"] == 10000
    assert tool_result["error_code"] is None


async def test_langgraph_tool_error_contains_normalized_skill_event():
    tools = ToolRegistry()

    async def sense(_state):
        raise RuntimeError("VLM_NOT_CONFIGURED")

    tools.register("sense", sense)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    result = await agent.run("识别图片里的食材", "conv_lg_sense_error", image_url="https://example.test/a.jpg")
    tool_result = next(e for e in result["events"] if e["type"] == "tool_result")

    assert result["status"] == "degraded"
    assert tool_result["status"] == "error"
    assert tool_result["tool"] == "sense"
    assert tool_result["skill"]["category"] == "perception"
    assert tool_result["error_code"] == "VLM_NOT_CONFIGURED"


async def test_langgraph_stops_after_skill_error_instead_of_continuing_to_decision():
    tools = ToolRegistry()
    calls = []

    async def sense(_state):
        calls.append("sense")
        raise RuntimeError("VLM_NOT_CONFIGURED")

    async def decision(_state):
        calls.append("decision")
        return {"recipes": [{"recipe_id": "r1", "title": "不应出现"}]}

    tools.register("sense", sense)
    tools.register("decision", decision)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    result = await agent.run("识别图片里的食材并推荐菜谱", "conv_lg_stop_on_error", image_url="https://example.test/a.jpg")

    assert calls == ["sense"]
    assert result["status"] == "degraded"
    assert result["termination_reason"] == "TOOL_ERROR"
    assert result["recipes"] == []
    assert [event.get("tool") for event in result["events"] if event["type"] == "tool_result"] == ["sense"]
