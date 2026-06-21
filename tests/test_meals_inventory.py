import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client):
    openid = f"meal_flow_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    data = resp.json()["data"]
    return {"Authorization": f"Bearer {data['token']}"}


async def test_plan_does_not_count_until_completed_and_deducts_inventory(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    inv = await client.post("/v1/inventory/import", headers=headers, json={
        "items": [
            {"name": "猪肉", "amount": 300, "unit": "g", "freshness": "normal"},
            {"name": "青椒", "amount": 3, "unit": "个", "freshness": "high"},
        ],
        "source": "test",
    })
    assert inv.status_code == 200
    assert inv.json()["data"]["count"] == 2

    before = await client.get("/v1/nutrition/summary?range=day", headers=headers)
    assert before.status_code == 200
    assert before.json()["data"]["totals"]["calories"] == 0
    assert "targets" in before.json()["data"]

    plan = await client.post("/v1/meals/plan", headers=headers, json={
        "meal_slot": "lunch",
        "recipe": {
            "recipe_id": "r_test",
            "title": "青椒肉丝",
            "calories": 260,
            "macros": {"protein": 24, "carbs": 10, "fat": 16},
            "micronutrients": {"fiber": 2, "vitamin_c": 8, "iron": 3.9},
            "ingredients": [
                {"name": "猪肉", "amount": "200g"},
                {"name": "青椒", "amount": "2个"},
            ],
        },
        "ingredients_used": [
            {"name": "猪肉", "amount": 200, "unit": "g"},
            {"name": "青椒", "amount": 2, "unit": "个"},
        ],
    })
    assert plan.status_code == 200
    meal = plan.json()["data"]["meal"]
    assert meal["status"] == "planned"

    planned_summary = await client.get("/v1/nutrition/summary?range=day", headers=headers)
    assert planned_summary.json()["data"]["totals"]["calories"] == 0

    completed = await client.post(f"/v1/meals/{meal['id']}/complete", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["data"]["meal"]["status"] == "completed"

    after = await client.get("/v1/nutrition/summary?range=day", headers=headers)
    totals = after.json()["data"]["totals"]
    assert totals["calories"] == 260
    assert totals["protein"] == 24

    current = await client.get("/v1/inventory/current", headers=headers)
    items = {item["name"]: item for item in current.json()["data"]["items"]}
    assert items["猪肉"]["amount"] == 100
    assert items["青椒"]["amount"] == 1
