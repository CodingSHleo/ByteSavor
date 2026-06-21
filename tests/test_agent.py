from app.services.agent import _parse_intent_regex
import pytest


def test_parse_intent_fat_loss():
    intent = _parse_intent_regex("家里有牛肉和南瓜，30分钟做个减脂餐")
    assert intent["goal"] == "fat_loss"
    assert intent["time_limit"] == 30
    assert "牛肉" in intent["ingredients"]
    assert "南瓜" in intent["ingredients"]


def test_parse_intent_extracts_specific_library_ingredients():
    intent = _parse_intent_regex("牛肉韭黄，推荐一道减脂晚餐")
    assert intent["goal"] == "fat_loss"
    assert "牛肉" in intent["ingredients"]
    assert "韭黄" in intent["ingredients"]


def test_parse_intent_muscle_gain():
    intent = _parse_intent_regex("增肌餐，15分钟，有鸡胸肉和鸡蛋")
    assert intent["goal"] == "muscle_gain"
    assert intent["time_limit"] == 15


def test_parse_intent_spicy():
    intent = _parse_intent_regex("想吃辣的")
    assert intent["taste"] == "spicy"


def test_parse_intent_default():
    intent = _parse_intent_regex("随便吃点东西")
    assert intent["goal"] == "balanced"
    assert intent["time_limit"] == 30


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_execute_returns_reply_text(client):
    resp = await client.post("/v1/agent/execute", json={
        "input": "牛肉南瓜减脂30分钟",
        "mode": "recommend"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["reply"]
    assert "recipes" in data["data"]


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_api_returns_dynamic_events_and_conversation_id(client, monkeypatch):
    async def fake_recommend(_db, _ingredients, _constraints, _preferences):
        return [{"recipe_id": "r_001", "title": "南瓜牛肉", "match_score": 0.91}]

    monkeypatch.setattr("app.routers.agent.recommend", fake_recommend)

    resp = await client.post("/v1/agent/execute", json={
        "input": "牛肉南瓜减脂30分钟，推荐一道菜",
        "mode": "full",
        "conversation_id": "conv_api_events",
    })

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["conversation_id"] == "conv_api_events"
    assert data["trace_id"]
    assert any(event["type"] == "plan" for event in data["events"])
    assert any(event["type"] == "tool_start" for event in data["events"])
    assert any(event["type"] == "tool_result" for event in data["events"])
    plan = next(event for event in data["events"] if event["type"] == "plan")
    assert "decision" in plan["available_skills"]
    tool_result = next(event for event in data["events"] if event["type"] == "tool_result")
    assert tool_result["skill"]["category"] == "decision"
    assert data["next_action"] == "complete"


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_api_asks_for_missing_image(client):
    resp = await client.post("/v1/agent/execute", json={
        "input": "帮我识别这张图片里的食材",
        "mode": "full",
        "conversation_id": "conv_api_ask",
    })

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "needs_input"
    assert data["next_action"] == "ask_user"
    assert data["events"][-1]["type"] == "ask_user"


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_api_keeps_recipe_context_across_turns(client, monkeypatch):
    decision_calls = []

    async def fake_recommend(_db, _ingredients, _constraints, _preferences):
        decision_calls.append("decision")
        return [{"recipe_id": "r_001", "title": "南瓜牛肉", "match_score": 0.91}]

    async def fake_merge(_db, recipe_ids):
        assert recipe_ids == ["r_001"]
        return [{"name": "牛肉", "display": "300g"}]

    monkeypatch.setattr("app.routers.agent.recommend", fake_recommend)
    monkeypatch.setattr("app.routers.agent.merge_shopping_list", fake_merge)
    conversation_id = "conv_api_multiturn"

    first = await client.post("/v1/agent/execute", json={
        "input": "推荐一道牛肉菜",
        "conversation_id": conversation_id,
    })
    second = await client.post("/v1/agent/execute", json={
        "input": "把刚才的菜生成购物清单",
        "conversation_id": conversation_id,
    })

    assert first.json()["data"]["recipes"][0]["recipe_id"] == "r_001"
    assert second.json()["data"]["shopping_list"][0]["name"] == "牛肉"
    assert decision_calls == ["decision"]


@pytest.mark.asyncio(loop_scope="session")
async def test_agent_api_sense_registered_and_degrades_when_vlm_not_configured(client, monkeypatch):
    monkeypatch.setattr("app.routers.agent.settings.vlm_api_url", "")

    resp = await client.post("/v1/agent/execute", json={
        "input": "识别图片里的食材",
        "mode": "full",
        "conversation_id": "conv_api_sense_no_vlm",
        "image_url": "https://example.test/food.jpg",
    })

    assert resp.status_code == 200
    data = resp.json()["data"]
    tool_result = next(event for event in data["events"] if event.get("type") == "tool_result")

    assert data["status"] == "degraded"
    assert tool_result["tool"] == "sense"
    assert tool_result["skill"]["category"] == "perception"
    assert tool_result["error_code"] == "VLM_NOT_CONFIGURED"
