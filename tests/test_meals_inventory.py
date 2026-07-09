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


async def test_adopt_recipe_deducts_inventory_once_and_returns_agent_trace(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    inv = await client.post("/v1/inventory/import", headers=headers, json={
        "items": [
            {"name": "牛肉", "amount": 250, "unit": "g", "freshness": "normal"},
            {"name": "韭黄", "amount": 100, "unit": "g", "freshness": "high"},
        ],
        "source": "test",
    })
    assert inv.status_code == 200

    adopted = await client.post("/v1/meals/adopt", headers=headers, json={
        "meal_slot": "dinner",
        "recipe": {
            "recipe_id": "r_beef_chive",
            "title": "韭黄炒牛肉",
            "calories": 360,
            "macros": {"protein": 32, "carbs": 14, "fat": 18},
            "ingredients": [
                {"name": "牛肉", "amount": "200g"},
                {"name": "韭黄", "amount": "150g"},
                {"name": "姜", "amount": "5g"},
            ],
        },
    })
    assert adopted.status_code == 200
    data = adopted.json()["data"]
    meal = data["meal"]
    assert meal["status"] == "planned"
    assert meal["meal_slot"] == "dinner"
    assert meal["recipe"]["_agent_inventory_applied"] is True
    assert meal["recipe"]["_agent_action"] == "adopt_recipe"
    assert {"name": "牛肉", "amount": 200, "unit": "g"} in meal["ingredients_used"]
    assert data["inventory_preview"]["deductions"][0]["name"] == "牛肉"
    assert any(item["name"] == "韭黄" and item["amount"] == 50 for item in data["shopping_list"])
    assert any(item["name"] == "姜" and item["amount"] == 5 for item in data["shopping_list"])
    assert any(event["stage"] == "inventory" for event in data["agent_events"])

    current = await client.get("/v1/inventory/current", headers=headers)
    items = {item["name"]: item for item in current.json()["data"]["items"]}
    assert items["牛肉"]["amount"] == 50
    assert items["韭黄"]["amount"] == 0

    completed = await client.post(f"/v1/meals/{meal['id']}/complete", headers=headers)
    assert completed.status_code == 200
    current_after_complete = await client.get("/v1/inventory/current", headers=headers)
    items_after = {item["name"]: item for item in current_after_complete.json()["data"]["items"]}
    assert items_after["牛肉"]["amount"] == 50
    assert items_after["韭黄"]["amount"] == 0


async def test_adopt_recipe_matches_inventory_by_synonym_and_exposes_shopping_summary(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    await client.post("/v1/inventory/import", headers=headers, json={
        "items": [
            {"name": "韭菜黄", "amount": 120, "unit": "g"},
            {"name": "姜", "amount": 10, "unit": "g"},
        ],
        "source": "test",
    })

    adopted = await client.post("/v1/meals/adopt", headers=headers, json={
        "meal_slot": "lunch",
        "recipe": {
            "recipe_id": "r_chive_alias",
            "title": "韭黄炒蛋",
            "ingredients": [
                {"name": "韭黄", "amount": "80g"},
                {"name": "鸡蛋", "amount": "2个"},
                {"name": "生姜", "amount": "5g"},
            ],
        },
    })

    assert adopted.status_code == 200
    data = adopted.json()["data"]
    deducted = {item["name"]: item for item in data["inventory_preview"]["deductions"]}
    assert "韭黄" in deducted
    assert deducted["韭黄"]["matched_inventory_name"] == "韭菜黄"
    assert "生姜" in deducted
    assert deducted["生姜"]["matched_inventory_name"] == "姜"
    assert any(item["name"] == "鸡蛋" and item["amount"] == 2 for item in data["shopping_list"])

    summary = await client.get("/v1/shopping-list/today", headers=headers)
    assert summary.status_code == 200
    items = summary.json()["data"]["items"]
    egg = next(item for item in items if item["name"] == "鸡蛋")
    assert egg["amount"] == 2
    assert egg["ids"]
    assert egg["sources"][0]["recipe_id"] == "r_chive_alias"


async def test_shopping_list_item_status_changes_are_persisted(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    adopted = await client.post("/v1/meals/adopt", headers=headers, json={
        "meal_slot": "dinner",
        "recipe": {
            "recipe_id": "r_shop_status",
            "title": "番茄鸡蛋面",
            "ingredients": [
                {"name": "番茄", "amount": "2个"},
                {"name": "鸡蛋", "amount": "2个"},
            ],
        },
    })
    assert adopted.status_code == 200

    summary = await client.get("/v1/shopping-list/today", headers=headers)
    assert summary.status_code == 200
    items = summary.json()["data"]["items"]
    tomato = next(item for item in items if item["name"] == "番茄")
    tomato_id = tomato["ids"][0]

    purchased = await client.put(
        f"/v1/shopping-list/items/{tomato_id}",
        headers=headers,
        json={"status": "purchased"},
    )
    assert purchased.status_code == 200
    assert purchased.json()["data"]["item"]["status"] == "purchased"

    after_purchase = await client.get("/v1/shopping-list/today", headers=headers)
    names_after_purchase = [item["name"] for item in after_purchase.json()["data"]["items"]]
    assert "番茄" not in names_after_purchase
    assert "鸡蛋" in names_after_purchase

    restored = await client.put(
        f"/v1/shopping-list/items/{tomato_id}",
        headers=headers,
        json={"status": "open"},
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["item"]["status"] == "open"

    after_restore = await client.get("/v1/shopping-list/today", headers=headers)
    assert "番茄" in [item["name"] for item in after_restore.json()["data"]["items"]]

    deleted = await client.delete(f"/v1/shopping-list/items/{tomato_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"]["item"]["status"] == "deleted"

    archived = await client.post("/v1/shopping-list/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["data"]["archived_count"] >= 1

    final_summary = await client.get("/v1/shopping-list/today", headers=headers)
    assert final_summary.json()["data"]["items"] == []
