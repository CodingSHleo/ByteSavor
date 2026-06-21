import asyncio

import pytest

from app.agent.state import new_agent_state
from app.agent.tools import ToolRegistry, execute_tool


pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_registry_registers_known_skill_and_exposes_descriptor():
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": []}

    tools.register("decision", decision)

    assert tools.has("decision") is True
    assert tools.get("decision") is decision
    assert tools.descriptor("decision").category == "decision"


async def test_registry_rejects_unknown_skill():
    tools = ToolRegistry()

    async def unknown(_state):
        return {}

    with pytest.raises(ValueError, match="Unknown skill descriptor: unknown"):
        tools.register("unknown", unknown)


async def test_registry_describe_returns_frontend_safe_descriptor_fields():
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": []}

    tools.register("decision", decision)
    desc = tools.describe()[0]

    assert desc["name"] == "decision"
    assert desc["category"] == "decision"
    assert desc["requires_image"] is False
    assert desc["requires_user"] is False
    assert "input_fields" in desc
    assert "output_fields" in desc
    assert "intent_keywords" in desc
    assert "completion_criteria" in desc
    assert desc["timeout_ms"] == 10000
    assert desc["max_retries"] == 0


async def test_registry_descriptor_for_sense_requires_image():
    tools = ToolRegistry()

    async def sense(_state):
        return {"ingredients": []}

    tools.register("sense", sense)

    assert tools.descriptor("sense").requires_image is True


async def test_execute_tool_success_returns_status_latency_and_descriptor():
    tools = ToolRegistry()

    async def decision(_state):
        return {"recipes": [{"recipe_id": "r1"}]}

    tools.register("decision", decision)
    state = new_agent_state("推荐一道菜", "conv_skill_success")

    result = await execute_tool(tools, "decision", state)

    assert result.status == "success"
    assert result.output == {"recipes": [{"recipe_id": "r1"}]}
    assert result.latency_ms >= 0
    assert result.retry_count == 0
    assert result.error_code is None
    assert result.descriptor["name"] == "decision"


async def test_execute_tool_timeout_returns_normalized_error_code():
    tools = ToolRegistry()

    async def inventory(_state):
        await asyncio.sleep(0.02)
        return {"items": []}

    tools.register("inventory", inventory)
    descriptor = tools.descriptor("inventory")
    original_timeout = descriptor.timeout_ms
    descriptor.timeout_ms = 1
    state = new_agent_state("看库存", "conv_skill_timeout")

    try:
        result = await execute_tool(tools, "inventory", state)
    finally:
        descriptor.timeout_ms = original_timeout

    assert result.status == "error"
    assert result.error_code == "TimeoutError"
    assert result.latency_ms >= 0


async def test_execute_tool_retries_retryable_error_once():
    tools = ToolRegistry()
    calls = {"count": 0}

    async def sense(_state):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("VLM_UNAVAILABLE")
        return {"ingredients": [{"name": "番茄"}]}

    tools.register("sense", sense)
    state = new_agent_state("识别图片", "conv_skill_retry", image_url="https://example.test/a.jpg")

    result = await execute_tool(tools, "sense", state)

    assert result.status == "success"
    assert result.retry_count == 1
    assert calls["count"] == 2
    assert result.output["ingredients"][0]["name"] == "番茄"
