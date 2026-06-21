import pytest

from app.agent.langgraph_runtime import LangGraphAgent
from app.agent.runtime import AgentRuntime
from app.agent.tools import ToolRegistry


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_soft_judge_warn_does_not_block_runtime(monkeypatch):
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": [{"recipe_id": "db_1", "title": "牛肉韭黄"}]}

    tools.register("decision", decision)
    async def fake_judge(_state):
        return {
            "verdict": "WARN",
            "scores": {"instruction_following": 3.5},
            "issues": ["偏好解释不足"],
            "suggestions": ["补充原因"],
        }

    monkeypatch.setattr("app.agent.runtime.judge_agent_result", fake_judge)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run("推荐一道牛肉韭黄", "conv_judge_warn")

    assert result["status"] == "success"
    assert result["termination_reason"] == "GOAL_ACHIEVED"
    types = [event["type"] for event in result["events"]]
    assert types.index("evaluation") < types.index("soft_judge") < types.index("final")
    judge_event = next(event for event in result["events"] if event["type"] == "soft_judge")
    assert judge_event["verdict"] == "WARN"


async def test_soft_judge_exception_records_event_without_blocking(monkeypatch):
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": [{"recipe_id": "db_2", "title": "韭黄炒蛋"}]}

    async def broken_judge(_state):
        raise RuntimeError("judge unavailable")

    tools.register("decision", decision)
    monkeypatch.setattr("app.agent.runtime.judge_agent_result", broken_judge)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run("推荐一道韭黄炒蛋", "conv_judge_exception")

    assert result["status"] == "success"
    assert result["termination_reason"] == "GOAL_ACHIEVED"
    judge_event = next(event for event in result["events"] if event["type"] == "soft_judge")
    assert judge_event["verdict"] == "SKIPPED"
    assert result["errors"] == []


async def test_langgraph_soft_judge_warn_does_not_change_status_or_reason(monkeypatch):
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": [{"recipe_id": "db_3", "title": "数据库候选"}]}

    tools.register("decision", decision)
    async def fake_judge(_state):
        return {"verdict": "WARN", "scores": {}, "issues": ["warn"], "suggestions": []}

    monkeypatch.setattr("app.agent.runtime.judge_agent_result", fake_judge)

    agent = LangGraphAgent(tools=tools, max_steps=4)
    result = await agent.run("推荐一道菜", "conv_lg_judge_warn")

    assert result["status"] == "success"
    assert result["termination_reason"] == "GOAL_ACHIEVED"
    types = [event["type"] for event in result["events"]]
    assert types.index("evaluation") < types.index("soft_judge") < types.index("final")


async def test_judge_cannot_invent_recipe_id(monkeypatch):
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": [{"recipe_id": "db_only", "title": "数据库菜谱"}]}

    tools.register("decision", decision)
    async def fake_judge(_state):
        return {
            "verdict": "WARN",
            "scores": {},
            "issues": ["建议 made_up_recipe"],
            "suggestions": ["不要新增菜谱"],
        }

    monkeypatch.setattr("app.agent.runtime.judge_agent_result", fake_judge)

    runtime = AgentRuntime(tools=tools)
    result = await runtime.run("推荐一道菜", "conv_judge_no_forge")

    assert [recipe["recipe_id"] for recipe in result["recipes"]] == ["db_only"]
