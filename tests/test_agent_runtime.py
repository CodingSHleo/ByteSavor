import pytest

from app.agent.runtime import AgentRuntime
from app.agent.tools import ToolRegistry


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_recommendation_uses_decision_without_unrequested_task():
    calls = []
    tools = ToolRegistry()

    async def decision(state):
        calls.append("decision")
        return {
            "recipes": [
                {"recipe_id": "r_001", "title": "南瓜牛肉", "match_score": 0.91}
            ]
        }

    async def task(state):
        calls.append("task")
        return {"shopping_list": [{"name": "牛肉", "display": "300g"}]}

    tools.register("decision", decision)
    tools.register("task", task)
    runtime = AgentRuntime(tools=tools)

    result = await runtime.run(
        user_input="牛肉南瓜减脂30分钟，推荐一道菜",
        conversation_id="conv_recommend",
    )

    assert calls == ["decision"]
    assert result["recipes"][0]["recipe_id"] == "r_001"
    event_types = [event["type"] for event in result["events"]]
    assert event_types[:4] == ["plan", "tool_start", "tool_result", "evaluation"]
    assert "final" in event_types  # P1-3: evaluation 在 final 之前


async def test_shopping_request_replans_from_decision_to_task():
    calls = []
    tools = ToolRegistry()

    async def decision(state):
        calls.append("decision")
        return {
            "recipes": [
                {"recipe_id": "r_001", "title": "香辣牛肉", "match_score": 0.88},
                {"recipe_id": "r_003", "title": "南瓜炖牛肉", "match_score": 0.81},
            ]
        }

    async def task(state):
        calls.append("task")
        assert [r["recipe_id"] for r in state["recipes"]] == ["r_001", "r_003"]
        return {"shopping_list": [{"name": "牛肉", "display": "700g"}]}

    tools.register("decision", decision)
    tools.register("task", task)
    runtime = AgentRuntime(tools=tools)

    result = await runtime.run(
        user_input="牛肉和南瓜做两道菜，再帮我生成购物清单",
        conversation_id="conv_shopping",
    )

    assert calls == ["decision", "task"]
    assert result["shopping_list"] == [{"name": "牛肉", "display": "700g"}]
    assert [e["tool"] for e in result["events"] if e["type"] == "tool_start"] == [
        "decision",
        "task",
    ]


async def test_image_intent_asks_for_image_when_missing():
    tools = ToolRegistry()
    runtime = AgentRuntime(tools=tools)

    result = await runtime.run(
        user_input="帮我识别这张图片里的食材",
        conversation_id="conv_missing_image",
    )

    assert result["status"] == "needs_input"
    assert result["next_action"] == "ask_user"
    assert result["events"][-1]["type"] == "ask_user"
    assert "图片" in result["events"][-1]["message"]


async def test_image_recommendation_uses_sense_result_for_decision():
    calls = []
    tools = ToolRegistry()

    async def sense(state):
        calls.append("sense")
        return {"ingredients": [{"name": "番茄"}, {"name": "鸡蛋"}]}

    async def decision(state):
        calls.append("decision")
        assert state["ingredients"] == ["番茄", "鸡蛋"]
        return {
            "recipes": [
                {"recipe_id": "r_002", "title": "番茄炒蛋", "match_score": 0.95}
            ]
        }

    tools.register("sense", sense)
    tools.register("decision", decision)
    runtime = AgentRuntime(tools=tools)

    result = await runtime.run(
        user_input="识别图片里的食材并推荐菜谱",
        image_url="data:image/jpeg;base64,dGVzdA==",
        conversation_id="conv_image_recommend",
    )

    assert calls == ["sense", "decision"]
    assert result["ingredients"] == ["番茄", "鸡蛋"]
    assert result["recipes"][0]["title"] == "番茄炒蛋"


async def test_same_conversation_has_distinct_trace_ids():
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": []}

    tools.register("decision", decision)
    runtime = AgentRuntime(tools=tools)

    first = await runtime.run("推荐一道菜", conversation_id="conv_same")
    second = await runtime.run("再推荐一道菜", conversation_id="conv_same")

    assert first["conversation_id"] == second["conversation_id"] == "conv_same"
    assert first["trace_id"] != second["trace_id"]

