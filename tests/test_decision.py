import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_meal_plan_with_ingredients(client):
    resp = await client.post("/v1/decision/meal-plan", json={
        "ingredients": ["牛肉", "西兰花"],
        "constraints": {"time_limit": 30, "taste": "spicy", "goal": "fat_loss"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    recipes = data["data"]["recipes"]
    assert len(recipes) > 0
    for r in recipes:
        assert "recipe_id" in r
        assert "match_score" in r
        assert "reasons" in r


async def test_meal_plan_empty_ingredients(client):
    resp = await client.post("/v1/decision/meal-plan", json={
        "ingredients": [],
        "constraints": {}
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    assert len(resp.json()["data"]["recipes"]) > 0


async def test_recipe_detail_found(client):
    resp = await client.get("/v1/recipes/r_001")
    assert resp.status_code == 200
    assert "香辣" in resp.json()["data"]["title"]


async def test_recipe_detail_not_found(client):
    resp = await client.get("/v1/recipes/r_999")
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "NOT_FOUND"
