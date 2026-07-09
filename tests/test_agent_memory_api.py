"""V3-3: MemoryContext previous_state API级回归测试。
证明同一 conversation_id 第二轮能看到第一轮状态。
包含 runtime 级和真实 API 级测试。"""
import uuid
import pytest
from app.agent.langgraph_runtime import LangGraphAgent
from app.agent.tools import ToolRegistry

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_memory_context_uses_previous_conversation_state():
    """同一 conversation 第二轮，memory_context 应包含上一轮菜谱。"""
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r_001", "title": "南瓜牛肉饭", "match_score": 0.9}]}

    tools.register("decision", decision)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    # 第一轮
    result1 = await agent.run(
        "牛肉南瓜减脂30分钟",
        conversation_id="conv_memory_api_test",
        memory_context={},
    )

    # 第二轮：取 previous_state
    prev = await agent.get_previous_state("conv_memory_api_test")
    assert prev is not None, "get_previous_state 应返回上一轮状态"
    assert "南瓜牛肉饭" in str(prev.get("recipes", [])), f"上一轮菜谱应包含南瓜牛肉饭，实际: {prev.get('recipes', [])}"

    # 第二轮执行
    result2 = await agent.run(
        "那换个更快的",
        conversation_id="conv_memory_api_test",
        memory_context={
            "conversation_memory": {
                "last_ingredients": prev.get("ingredients", []),
                "last_recipes": [r.get("title", "") for r in prev.get("recipes", [])[:3]],
                "last_user_goal": prev.get("intent", {}).get("goal", ""),
            },
            "preference_memory": {},
            "fact_memory": {},
            "correction_memory": {},
        },
    )

    conv_mem = result2.get("memory_context", {}).get("conversation_memory", {})
    last_recipes = conv_mem.get("last_recipes", [])
    assert len(last_recipes) > 0, f"第二轮 memory_context 应有上一轮菜谱，实际: {last_recipes}"
    assert "南瓜牛肉饭" in last_recipes, f"应包含南瓜牛肉饭，实际: {last_recipes}"


async def test_memory_context_persists_in_result():
    """memory_context 和 memory_used 应在 runtime 结果中返回。"""
    tools = ToolRegistry()

    async def decision(state):
        return {"recipes": [{"recipe_id": "r_002", "title": "减脂牛肉沙拉", "match_score": 0.85}]}

    tools.register("decision", decision)
    agent = LangGraphAgent(tools=tools, max_steps=4)

    result = await agent.run(
        "推荐减脂餐",
        conversation_id="conv_memory_persist",
        memory_context={
            "conversation_memory": {"last_ingredients": ["牛肉"], "last_recipes": [], "last_user_goal": "fat_loss"},
            "preference_memory": {"liked_tags": ["high_protein"], "avoid_tags": [], "liked_ingredients": [], "avoid_ingredients": []},
            "fact_memory": {"inventory": [], "today_nutrition_gap": {}, "planned_meals": []},
            "correction_memory": {"recent_aliases": []},
        },
    )

    assert "memory_context" in result, "result 应有 memory_context"
    assert "memory_used" in result, "result 应有 memory_used"
    assert isinstance(result["memory_used"], list)


# ── 真实 API 级测试：使用 FastAPI TestClient ──
async def test_api_agent_returns_memory_context(client):
    """V3: 真实 /v1/agent/execute 请求应返回 memory_context 和 memory_used。"""
    resp = await client.post("/v1/agent/execute", json={
        "input": "牛肉南瓜减脂30分钟",
        "conversation_id": f"api_mem_{uuid.uuid4().hex[:8]}",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "memory_context" in data, f"API 应返回 memory_context, keys: {list(data.keys())[:10]}"
    assert "memory_used" in data, "API 应返回 memory_used"
    assert isinstance(data["memory_used"], list)


async def test_api_agent_second_round_sees_previous(client):
    """V3: 同一 conversation_id 第二轮应能看到上一轮菜谱。"""
    conv_id = f"api_2round_{uuid.uuid4().hex[:8]}"

    # 第一轮
    r1 = await client.post("/v1/agent/execute", json={
        "input": "牛肉南瓜减脂30分钟",
        "conversation_id": conv_id,
    })
    assert r1.status_code == 200
    d1 = r1.json()["data"]
    assert "recipes" in d1

    # 第二轮
    r2 = await client.post("/v1/agent/execute", json={
        "input": "那换个更快的",
        "conversation_id": conv_id,
    })
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    assert "memory_used" in d2
    # conversation memory 应包含上轮信息 OR memory_used 有 conversation 条目
    conv_mem = d2.get("memory_context", {}).get("conversation_memory", {})
    mem_used_types = [m.get("type") for m in d2.get("memory_used", [])]
    has_conv_memory = (
        len(conv_mem.get("last_ingredients", [])) > 0
        or len(conv_mem.get("last_recipes", [])) > 0
        or "conversation" in mem_used_types
    )
    assert has_conv_memory, (
        f"第二轮应看到上一轮记忆。"
        f" last_ingredients={conv_mem.get('last_ingredients')},"
        f" last_recipes={conv_mem.get('last_recipes')},"
        f" memory_used_types={mem_used_types}"
    )


async def test_api_agent_new_explicit_ingredients_do_not_reuse_previous_recipes(client, monkeypatch):
    """同一 conversation_id 中，如果本轮明确输入新食材，必须重新推荐而不是复用上一轮菜谱。"""
    calls = []

    async def fake_recommend(_db, ingredients, _constraints, _prefs):
        calls.append(list(ingredients))
        if "番茄" in ingredients:
            return [{
                "recipe_id": "r_tomato_beef",
                "title": "番茄牛肉",
                "match_score": 0.95,
                "ingredients": [{"name": "番茄"}, {"name": "牛肉"}],
                "_meta": {"matched_user_ingredients": ["番茄", "牛肉"], "missing_user_ingredients": []},
            }]
        return [{
            "recipe_id": "r_pepper_beef",
            "title": "青椒牛肉",
            "match_score": 0.8,
            "ingredients": [{"name": "青椒"}, {"name": "牛肉"}],
            "_meta": {"matched_user_ingredients": ["青椒", "牛肉"], "missing_user_ingredients": []},
        }]

    monkeypatch.setattr("app.routers.agent.recommend", fake_recommend)
    conv_id = f"api_new_food_{uuid.uuid4().hex[:8]}"

    first = await client.post("/v1/agent/execute", json={
        "input": "青椒牛肉减脂30分钟",
        "conversation_id": conv_id,
    })
    second = await client.post("/v1/agent/execute", json={
        "input": "番茄牛肉减脂30分钟",
        "conversation_id": conv_id,
    })

    assert first.status_code == 200
    assert second.status_code == 200
    d2 = second.json()["data"]
    assert d2["recipes"][0]["recipe_id"] == "r_tomato_beef"
    assert d2["parsed_intent"]["ingredients"] == ["牛肉", "番茄"]
    assert calls == [["牛肉", "青椒"], ["牛肉", "番茄"]]
