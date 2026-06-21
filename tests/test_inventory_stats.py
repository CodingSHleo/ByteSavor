import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client, prefix="inventory_user"):
    openid = f"{prefix}_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_manual_inventory_add_update_delete_and_stats(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    created = await client.post("/v1/inventory/items", headers=headers, json={
        "name": "南瓜",
        "amount": 500,
        "unit": "g",
        "freshness": "high",
        "source": "manual",
    })
    assert created.status_code == 200
    item = created.json()["data"]["item"]
    assert item["name"] == "南瓜"
    assert item["amount"] == 500
    assert item["unit"] == "g"

    updated = await client.put(f"/v1/inventory/items/{item['id']}", headers=headers, json={
        "amount": 350,
        "unit": "g",
        "freshness": "normal",
    })
    assert updated.status_code == 200
    assert updated.json()["data"]["item"]["amount"] == 350
    assert updated.json()["data"]["item"]["freshness"] == "normal"

    stats = await client.get("/v1/inventory/stats", headers=headers)
    assert stats.status_code == 200
    data = stats.json()["data"]
    assert data["total_items"] >= 1
    assert data["by_source"]["manual"] >= 1
    assert data["by_freshness"]["normal"] >= 1

    deleted = await client.delete(f"/v1/inventory/items/{item['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    current = await client.get("/v1/inventory/current", headers=headers)
    assert all(row["id"] != item["id"] for row in current.json()["data"]["items"])

