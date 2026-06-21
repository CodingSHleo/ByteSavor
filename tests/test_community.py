import time

import pytest
from app.core.database import Base, engine

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


async def _login(client, prefix):
    openid = f"{prefix}_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_recipe_post_like_comment_and_author_delete(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    author = await _login(client, "post_author")
    reader = await _login(client, "post_reader")

    created = await client.post("/v1/community/posts", headers=author, json={
        "title": "南瓜牛肉便当",
        "content": "适合训练后的一餐。",
        "category": "recipe",
        "images": [],
        "recipe_payload": {
            "title": "南瓜牛肉便当",
            "ingredients": [{"name": "牛肉", "amount": "120g"}, {"name": "南瓜", "amount": "150g"}],
            "steps": ["煎牛肉", "蒸南瓜", "装盒"],
            "calories": 420,
            "macros": {"protein": 35, "carbs": 42, "fat": 12},
        },
    })
    assert created.status_code == 200
    post_id = created.json()["data"]["post"]["id"]

    like_one = await client.post(f"/v1/community/posts/{post_id}/like", headers=reader)
    like_two = await client.post(f"/v1/community/posts/{post_id}/like", headers=reader)
    assert like_one.status_code == 200
    assert like_two.status_code == 200
    assert like_two.json()["data"]["liked"] is True

    comment = await client.post(f"/v1/community/posts/{post_id}/comments", headers=reader, json={
        "content": "这个可以加入我的减脂餐。"
    })
    assert comment.status_code == 200

    detail = await client.get(f"/v1/community/posts/{post_id}", headers=reader)
    assert detail.status_code == 200
    assert detail.json()["data"]["post"]["like_count"] == 1
    assert detail.json()["data"]["post"]["comment_count"] == 1

    forbidden = await client.delete(f"/v1/community/posts/{post_id}", headers=reader)
    assert forbidden.status_code in (200, 403)
    if forbidden.status_code == 200:
        assert forbidden.json()["status"] == "error"

    deleted = await client.delete(f"/v1/community/posts/{post_id}", headers=author)
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True



# ── v5: 错误语义 + 分页 + liked_by_me ──

async def test_community_delete_missing_post_returns_error(client):
    """删除不存在帖子返回 POST_NOT_FOUND。"""
    author = await _login(client, "del_missing")
    resp = await client.delete("/v1/community/posts/99999", headers=author)
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "POST_NOT_FOUND"


async def test_community_like_missing_post_returns_error(client):
    """点赞不存在帖子返回 POST_NOT_FOUND。"""
    reader = await _login(client, "like_missing")
    resp = await client.post("/v1/community/posts/99999/like", headers=reader)
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "POST_NOT_FOUND"


async def test_community_invalid_category_returns_error(client):
    """非法 category 返回 INVALID_CATEGORY。"""
    resp = await client.get("/v1/community/posts?category=bad")
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "INVALID_CATEGORY"


async def test_community_list_supports_pagination(client):
    """列表支持分页参数。"""
    author = await _login(client, "paginate")
    for i in range(3):
        await client.post("/v1/community/posts", headers=author, json={
            "title": f"分页测试帖{i}", "content": "test", "category": "health",
        })
    r1 = await client.get("/v1/community/posts?limit=2&offset=0")
    assert r1.status_code == 200
    data1 = r1.json()["data"]
    assert len(data1["posts"]) <= 2
    assert "total" in data1
    assert "has_more" in data1


async def test_community_list_includes_liked_by_me(client):
    """列表对登录用户返回 liked_by_me。"""
    author = await _login(client, "likedby")
    reader = await _login(client, "likedby_r")
    r = await client.post("/v1/community/posts", headers=author, json={
        "title": "liked_by_me 测试", "content": "t", "category": "checkin",
    })
    post_id = r.json()["data"]["post"]["id"]
    await client.post(f"/v1/community/posts/{post_id}/like", headers=reader)
    r2 = await client.get("/v1/community/posts", headers=reader)
    posts = r2.json()["data"]["posts"]
    target = [p for p in posts if p["id"] == post_id]
    assert len(target) == 1
    assert target[0]["liked_by_me"] is True


async def test_community_list_and_detail_include_favorited_by_me(client):
    """社区收藏状态应跨刷新、跨接口回显。"""
    author = await _login(client, "favby")
    reader = await _login(client, "favby_r")
    r = await client.post("/v1/community/posts", headers=author, json={
        "title": "favorited_by_me 测试", "content": "t", "category": "checkin",
    })
    post = r.json()["data"]["post"]
    post_id = str(post["id"])

    await client.post("/v1/favorites", headers=reader, json={
        "target_type": "community_post",
        "target_id": post_id,
        "snapshot": post,
    })

    listed = await client.get("/v1/community/posts", headers=reader)
    posts = listed.json()["data"]["posts"]
    target = [p for p in posts if str(p["id"]) == post_id]
    assert len(target) == 1
    assert target[0]["favorited_by_me"] is True

    detail = await client.get(f"/v1/community/posts/{post_id}", headers=reader)
    assert detail.json()["data"]["post"]["favorited_by_me"] is True


async def test_community_delete_forbidden(client):
    """非作者删除返回 FORBIDDEN。"""
    author = await _login(client, "fbd_auth")
    other = await _login(client, "fbd_other")
    r = await client.post("/v1/community/posts", headers=author, json={
        "title": "禁止删除测试", "content": "x", "category": "checkin",
    })
    post_id = r.json()["data"]["post"]["id"]
    resp = await client.delete(f"/v1/community/posts/{post_id}", headers=other)
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "FORBIDDEN"


async def test_community_empty_comment_returns_error(client):
    """空评论返回错误。"""
    author = await _login(client, "empty_cmt")
    r = await client.post("/v1/community/posts", headers=author, json={
        "title": "空评论测试", "content": "x", "category": "checkin",
    })
    post_id = r.json()["data"]["post"]["id"]
    resp = await client.post(f"/v1/community/posts/{post_id}/comments", headers=author, json={"content": ""})
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"


async def test_community_unlike_decreases_count(client):
    """取消点赞减少计数。"""
    author = await _login(client, "unlike_auth")
    reader = await _login(client, "unlike_reader")
    r = await client.post("/v1/community/posts", headers=author, json={
        "title": "取消赞测试", "content": "x", "category": "checkin",
    })
    post_id = r.json()["data"]["post"]["id"]
    await client.post(f"/v1/community/posts/{post_id}/like", headers=reader)
    detail1 = await client.get(f"/v1/community/posts/{post_id}", headers=reader)
    assert detail1.json()["data"]["post"]["like_count"] == 1
    await client.delete(f"/v1/community/posts/{post_id}/like", headers=reader)
    detail2 = await client.get(f"/v1/community/posts/{post_id}", headers=reader)
    assert detail2.json()["data"]["post"]["like_count"] == 0
