import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client):
    openid = f"checker_user_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_recipe_check_returns_owned_missing_and_ratio(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    await client.post("/v1/inventory/import", headers=headers, json={
        "items": [
            {"name": "牛肉", "amount": 100, "unit": "g"},
            {"name": "南瓜", "amount": 50, "unit": "g"},
        ],
        "source": "test",
    })

    recipes = await client.get("/v1/recipes")
    assert recipes.status_code == 200
    target = next(
        r for r in recipes.json()["data"]["recipes"]
        if "牛肉" in r["title"] or "南瓜" in r["title"]
    )

    checked = await client.post("/v1/recipes/check", headers=headers, json={
        "target_type": "system_recipe",
        "target_id": target["recipe_id"],
    })
    assert checked.status_code == 200
    data = checked.json()["data"]
    assert data["target"]["title"]
    assert "owned" in data
    assert "missing" in data
    assert 0 <= data["fit_ratio"] <= 1
    assert isinstance(data["shopping_list"], list)

