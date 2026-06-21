import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client, prefix):
    openid = f"{prefix}_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_community_recipe_can_be_favorited_checked_and_planned(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    author = await _login(client, "community_author")
    user = await _login(client, "community_user")

    post = await client.post("/v1/community/posts", headers=author, json={
        "title": "社区南瓜牛肉",
        "content": "高蛋白快手菜。",
        "category": "recipe",
        "images": [],
        "recipe_payload": {
            "title": "社区南瓜牛肉",
            "ingredients": [{"name": "牛肉", "amount": "100g"}, {"name": "南瓜", "amount": "100g"}],
            "steps": ["炒牛肉", "加入南瓜"],
            "calories": 360,
            "macros": {"protein": 28, "carbs": 30, "fat": 12},
        },
    })
    post_id = str(post.json()["data"]["post"]["id"])

    await client.post("/v1/inventory/import", headers=user, json={
        "items": [{"name": "牛肉", "amount": 80, "unit": "g"}],
        "source": "test",
    })

    fav = await client.post("/v1/favorites", headers=user, json={
        "target_type": "community_post",
        "target_id": post_id,
        "snapshot": post.json()["data"]["post"],
    })
    assert fav.status_code == 200

    checked = await client.post("/v1/recipes/check", headers=user, json={
        "target_type": "community_post",
        "target_id": post_id,
    })
    assert checked.status_code == 200
    data = checked.json()["data"]
    assert data["target"]["title"] == "社区南瓜牛肉"
    assert any(item["name"] == "南瓜" for item in data["missing"])

