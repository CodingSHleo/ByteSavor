import pytest

from app.agent.langgraph_runtime import LangGraphAgent
from app.agent.tools import ToolRegistry


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_langgraph_executes_conditional_tool_loop():
    calls = []
    tools = ToolRegistry()

    async def decision(_state):
        calls.append("decision")
        return {"recipes": [{"recipe_id": "r_001", "title": "牛肉南瓜"}]}

    async def task(_state):
        calls.append("task")
        return {"shopping_list": [{"name": "牛肉", "display": "700g"}]}

    tools.register("decision", decision)
    tools.register("task", task)
    agent = LangGraphAgent(tools)

    result = await agent.run(
        "牛肉南瓜做两道菜并生成购物清单",
        conversation_id="graph_shopping",
    )

    assert calls == ["decision", "task"]
    assert result["next_action"] == "complete"
    assert result["shopping_list"][0]["display"] == "700g"
    assert agent.graph is not None


async def test_langgraph_interrupts_for_missing_image():
    agent = LangGraphAgent(ToolRegistry())

    result = await agent.run(
        "识别这张图片里的食材",
        conversation_id="graph_ask",
    )

    assert result["status"] == "needs_input"
    assert result["events"][-1]["type"] == "ask_user"


async def test_langgraph_reuses_previous_recipes_in_same_conversation():
    calls = []
    tools = ToolRegistry()

    async def decision(_state):
        calls.append("decision")
        return {"recipes": [{"recipe_id": "r_001", "title": "牛肉南瓜"}]}

    async def task(state):
        calls.append("task")
        assert state["recipes"][0]["recipe_id"] == "r_001"
        return {"shopping_list": [{"name": "牛肉", "display": "300g"}]}

    tools.register("decision", decision)
    tools.register("task", task)
    agent = LangGraphAgent(tools)

    await agent.run("推荐一道牛肉菜", conversation_id="graph_memory")
    result = await agent.run("把刚才的菜生成购物清单", conversation_id="graph_memory")

    assert calls == ["decision", "task"]
    assert result["shopping_list"][0]["name"] == "牛肉"
