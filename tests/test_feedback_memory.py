import uuid

import pytest
from sqlalchemy import select

from app.core.database import async_session
from app.models import PreferenceMemory
from app.services.feedback import get_preference_signals

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _register(client):
    resp = await client.post("/v1/auth/register", json={"openid": f"wx_pref_{uuid.uuid4().hex}"})
    assert resp.status_code == 200
    token = resp.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}, resp.json()["data"]["user_id"]


async def test_feedback_comment_creates_preference_memory(client):
    headers, user_id = await _register(client)

    resp = await client.post(
        "/v1/feedback/meal",
        headers=headers,
        json={
            "recipe_id": "scan_intake_test",
            "rating": 5,
            "comment": "喜欢清淡少油，高蛋白，牛肉口感好",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["acknowledged"] is True

    async with async_session() as db:
        result = await db.execute(
            select(PreferenceMemory).where(PreferenceMemory.user_id == user_id).order_by(PreferenceMemory.id.desc())
        )
        memory = result.scalars().first()
        assert memory is not None
        assert memory.rating == 5
        assert "高蛋白" in memory.comment
        assert "high_protein" in memory.parsed["liked_tags"]


async def test_preference_signals_include_like_and_avoid_memory(client):
    headers, user_id = await _register(client)

    await client.post(
        "/v1/feedback/meal",
        headers=headers,
        json={"recipe_id": "scan_like", "rating": 5, "comment": "喜欢香辣高蛋白"},
    )
    await client.post(
        "/v1/feedback/meal",
        headers=headers,
        json={"recipe_id": "scan_dislike", "rating": 2, "comment": "太油腻了，不想再吃"},
    )

    async with async_session() as db:
        signals = await get_preference_signals(db, user_id)

    assert "high_protein" in signals["liked_tags"]
    assert "oily" in signals["avoid_tags"]


async def test_feedback_with_recipe_snapshot_extracts_rich_preference_memory(client):
    headers, user_id = await _register(client)

    resp = await client.post(
        "/v1/feedback/meal",
        headers=headers,
        json={
            "recipe_id": "agent_snapshot_recipe",
            "rating": 5,
            "comment": "喜欢10分钟快炒，少油清淡，韭黄口感很好",
            "recipe_snapshot": {
                "title": "韭黄炒牛肉",
                "tags": ["quick", "high_protein"],
                "ingredients": [
                    {"name": "牛肉", "amount": "200g"},
                    {"name": "韭黄", "amount": "150g"},
                ],
                "steps": ["快炒牛肉", "加入韭黄"],
            },
        },
    )

    assert resp.status_code == 200
    async with async_session() as db:
        result = await db.execute(
            select(PreferenceMemory).where(PreferenceMemory.user_id == user_id).order_by(PreferenceMemory.id.desc())
        )
        memory = result.scalars().first()
        signals = await get_preference_signals(db, user_id)

    assert memory is not None
    assert "韭黄" in memory.parsed["liked_ingredients"]
    assert "stir_fry" in memory.parsed["liked_methods"]
    assert "quick_meal" in memory.parsed["constraints"]
    assert "low_oil" in memory.parsed["constraints"]
    assert "stir_fry" in signals["liked_methods"]
    assert "quick_meal" in signals["constraints"]
