import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client):
    openid = f"agent_tool_user_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_agent_uses_inventory_favorites_and_checker_tools(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    recipes = await client.get("/v1/recipes")
    recipe = recipes.json()["data"]["recipes"][0]
    await client.post("/v1/favorites", headers=headers, json={
        "target_type": "system_recipe",
        "target_id": recipe["recipe_id"],
        "snapshot": recipe,
    })

    resp = await client.post("/v1/agent/execute", headers=headers, json={
        "input": "我收藏的菜现在库存能不能做？缺什么？",
        "mode": "full",
        "conversation_id": f"agent_tool_test_{int(time.time() * 1000)}",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    tools = [event.get("tool") for event in data.get("events", []) if event.get("type") == "tool_result"]
    assert "inventory" in tools
    assert "favorites" in tools
    assert "recipe_check" in tools
    assert data.get("recipe_check") is not None

