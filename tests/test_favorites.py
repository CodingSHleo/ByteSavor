import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client, prefix):
    openid = f"{prefix}_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_system_recipe_favorite_is_persistent_and_user_scoped(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    user_a = await _login(client, "fav_a")
    user_b = await _login(client, "fav_b")

    recipes = await client.get("/v1/recipes")
    recipe = recipes.json()["data"]["recipes"][0]

    created = await client.post("/v1/favorites", headers=user_a, json={
        "target_type": "system_recipe",
        "target_id": recipe["recipe_id"],
        "snapshot": recipe,
    })
    assert created.status_code == 200
    assert created.json()["data"]["favorite"]["target_id"] == recipe["recipe_id"]

    duplicate = await client.post("/v1/favorites", headers=user_a, json={
        "target_type": "system_recipe",
        "target_id": recipe["recipe_id"],
        "snapshot": recipe,
    })
    assert duplicate.status_code == 200

    list_a = await client.get("/v1/favorites", headers=user_a)
    assert len(list_a.json()["data"]["favorites"]) == 1

    list_b = await client.get("/v1/favorites", headers=user_b)
    assert list_b.json()["data"]["favorites"] == []

    status = await client.get(
        f"/v1/favorites/status?target_type=system_recipe&target_id={recipe['recipe_id']}",
        headers=user_a,
    )
    assert status.json()["data"]["favorited"] is True

    deleted = await client.delete(
        f"/v1/favorites?target_type=system_recipe&target_id={recipe['recipe_id']}",
        headers=user_a,
    )
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

