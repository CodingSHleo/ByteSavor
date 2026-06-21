# Community Favorites Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build database-backed community posts, recipe favorites, recipe inventory checking, and inventory management so ByteSavor can connect recipes, users, community content, and meal completion into one executable diet loop.

**Architecture:** Extend the existing FastAPI + SQLAlchemy backend with focused routers/services for inventory, recipe checking, favorites, and community. Upgrade the uni-app frontend by turning the current Explore page into a recipe library, adding community/favorites/inventory/checker pages, and wiring every recipe card to the same favorite/check/plan actions. Keep existing meal completion as the only path that writes nutrition intake.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic, pytest/httpx, MySQL-compatible schema creation, Vue 3/uni-app, existing ApiService wrapper.

---

## Engineering Preflight

### Goal

Implement the next product layer without breaking the current B-Y-T-E flow:

识别/输入食材 -> 库存 -> 菜谱推荐/搜索 -> 菜谱清点 -> 购物清单/今日计划 -> 完成摄入 -> 营养记录 -> 评分偏好 -> 后续推荐。

### Current Evidence

- Existing DB models include users, profiles, inventory, meal records, nutrition logs, feedback and preference memories.
- Existing backend already has `/v1/inventory/import`, `/v1/inventory/current`, `/v1/meals/plan`, `/v1/meals/today`, `/v1/meals/{id}/complete`, `/v1/nutrition/summary`.
- Existing recipe endpoints are `/v1/recipes`, `/v1/recipes/{recipe_id}`, `/v1/decision/meal-plan`.
- Existing frontend tabBar is 首页 / 识别 / 探索 / 知识 / 我的.
- Existing Explore page can load true backend recipes, but only searches title locally and does not know inventory/favorites/community.
- Existing recipe detail favorite is not persisted.
- Existing tests prove plan does not count as intake until complete.

### Constraints

- Do not introduce password login as if it already exists. Current auth is openid + JWT demo auth.
- Do not make community import or favorite count as intake.
- Do not break existing demo pages: ingredient recognition, quality assessment, meal nutrition, food guide, text import.
- Do not reference missing icons. Add or reuse actual static assets.
- Worktree is dirty. Do not revert unrelated user changes.
- No production code without failing tests first for backend behavior changes.

### Boundaries

In scope:

- DB-backed favorites.
- DB-backed community MVP.
- Inventory manual CRUD and stats.
- Recipe search/check against inventory.
- Frontend pages and navigation for 菜谱 / 社区 / 我的收藏 / 库存 / 清点器.
- Agent tool upgrade plan and minimal tool wiring if existing planner shape allows.

Out of scope for this iteration:

- Full medical advice workflow.
- Real image object storage service.
- Password account system.
- Full unit conversion engine across arbitrary units.
- Content moderation pipeline.
- Production WeChat `code2session`.

### Negative Review

- Risk: implementing community first creates a cosmetic forum. Mitigation: implement inventory checker and favorites before community consumption.
- Risk: table creation without migrations can diverge on MySQL. Mitigation: follow existing startup compatibility helpers and tests.
- Risk: front-end state can split between storage and backend. Mitigation: new inventory/favorites/community state reads backend as source of truth.
- Risk: Agent remains weak if it cannot use new tools. Mitigation: expose backend service functions first, then add planner/tool tests.
- Risk: API grows too much. Mitigation: keep router boundaries small and avoid general-purpose social platform features.

### Verification

- Backend targeted pytest per task.
- Full backend regression subset after backend tasks.
- Frontend `npm run build:h5`.
- Browser smoke for tab navigation and key flows.
- Manual role demo script updated after implementation.

---

## File Structure

### Backend Creates

- `app/routers/inventory.py`: manual inventory CRUD and stats. Move or wrap existing inventory endpoints carefully.
- `app/services/inventory.py`: inventory normalization, add/update/delete/stats.
- `app/routers/recipe_tools.py`: recipe search and check endpoints.
- `app/services/recipe_checker.py`: compare system/community recipe requirements with user inventory.
- `app/routers/favorites.py`: favorite create/list/delete/status endpoints.
- `app/services/favorites.py`: favorite persistence, snapshots, status resolution.
- `app/routers/community.py`: community post/comment/like endpoints.
- `app/services/community.py`: community validation and ownership rules.
- `tests/test_inventory_stats.py`
- `tests/test_recipe_checker.py`
- `tests/test_favorites.py`
- `tests/test_community.py`
- `tests/test_agent_tools_inventory_favorites.py`

### Backend Modifies

- `app/models/__init__.py`: add CommunityPost, CommunityComment, CommunityLike, RecipeFavorite.
- `app/schemas.py`: add request/response schemas for inventory items, recipe checking, favorites, community.
- `app/main.py`: include new routers and run small compatibility table setup if needed.
- `app/routers/meals.py`: either delegate inventory endpoints to new service or keep compatibility wrappers.
- `app/services/meal_memory.py`: import inventory helper from new inventory service and keep completion semantics unchanged.
- `app/agent/tools.py` or existing Agent tool module: add inventory/favorites/recipe-check tools.
- `app/agent/planner.py` or planner-related service: route “收藏/库存/缺什么/能不能做” to new tools.

### Frontend Creates

- `bsapp/src/pages/inventory/inventory.vue`
- `bsapp/src/pages/recipe-checker/recipe-checker.vue`
- `bsapp/src/pages/favorites/favorites.vue`
- `bsapp/src/pages/community/community.vue`
- `bsapp/src/pages/community-detail/community-detail.vue`
- `bsapp/src/pages/community-publish/community-publish.vue`
- `bsapp/src/components/favorite-button.vue`
- `bsapp/src/components/community-post-card.vue`
- `bsapp/src/components/recipe-check-panel.vue`

### Frontend Modifies

- `bsapp/src/api/index.js`: add inventory CRUD, recipe check/search, favorites, community methods.
- `bsapp/src/pages.json`: tabBar becomes 首页 / 识别 / 菜谱 / 社区 / 我的. Existing knowledge page remains as non-tab page.
- `bsapp/src/pages/explore/explore.vue`: rename displayed title to 菜谱库 and add inventory/favorite/community filters.
- `bsapp/src/pages/home/home.vue`: add inventory/favorites/checker entries and favorite/check actions on recommended recipes.
- `bsapp/src/pages/recipe-detail/recipe-detail.vue`: real favorite status, check recipe, import missing, add to plan.
- `bsapp/src/pages/profile/profile.vue`: add favorites, inventory, my posts entries.
- `bsapp/src/components/recipe-card.vue`: add optional favorite/check action slots or emit actions without breaking old use.

---

## Task 1: Backend Inventory CRUD And Stats

**Files:**
- Create: `app/services/inventory.py`
- Create: `app/routers/inventory.py`
- Modify: `app/main.py`
- Modify: `app/routers/meals.py`
- Test: `tests/test_inventory_stats.py`

- [ ] **Step 1: Write failing tests for manual inventory CRUD**

Create `tests/test_inventory_stats.py` with tests covering:

```python
import time

import pytest
from app.core.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="session")


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
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_inventory_stats.py
```

Expected: FAIL because `/v1/inventory/items` and `/v1/inventory/stats` do not exist.

- [ ] **Step 3: Implement `app/services/inventory.py`**

Move reusable logic from `meal_memory.import_inventory`, `current_inventory`, `_parse_amount`, `_inventory_dict` into a focused service. Add:

```python
async def add_item(db, user_id, payload): ...
async def update_item(db, user_id, item_id, payload): ...
async def delete_item(db, user_id, item_id): ...
async def inventory_stats(db, user_id): ...
```

Keep existing import behavior compatible with scan/import flows.

- [ ] **Step 4: Implement router**

Create `app/routers/inventory.py` with:

- `POST /v1/inventory/items`
- `PUT /v1/inventory/items/{item_id}`
- `DELETE /v1/inventory/items/{item_id}`
- `GET /v1/inventory/stats`
- compatibility endpoints can remain in `meals.py`, but they should call the same service.

- [ ] **Step 5: Register router and run tests**

Modify `app/main.py` to include `inventory.router`.

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_inventory_stats.py tests/test_meals_inventory.py
```

Expected: PASS.

---

## Task 2: Recipe Checker And Search

**Files:**
- Create: `app/services/recipe_checker.py`
- Create: `app/routers/recipe_tools.py`
- Modify: `app/routers/decision.py`
- Modify: `app/main.py`
- Test: `tests/test_recipe_checker.py`

- [ ] **Step 1: Write failing tests for recipe check**

Create `tests/test_recipe_checker.py`:

```python
import time

import pytest
from app.core.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="session")


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
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_recipe_checker.py
```

Expected: FAIL because `/v1/recipes/check` does not exist.

- [ ] **Step 3: Implement checker service**

`recipe_checker.py` should:

- Load system recipe by `Recipe.id`.
- Later load community recipe by `CommunityPost.recipe_payload`.
- Normalize ingredient names using decision service matching rules or a shared helper.
- Parse amounts using inventory service helper.
- Return:

```python
{
    "target": {"target_type": "...", "target_id": "...", "title": "..."},
    "owned": [{"name": "...", "required": "...", "available": "..."}],
    "missing": [{"name": "...", "required": "...", "available": "...", "shortage": "..."}],
    "shopping_list": [{"name": "...", "amount": "..."}],
    "fit_ratio": 0.0,
    "can_cook": False,
}
```

- [ ] **Step 4: Implement recipe tools router**

Add `POST /v1/recipes/check`.

Extend `GET /v1/recipes` query handling in `decision.py` or route through `recipe_tools.py`:

- `q`: title/ingredient/tag contains.
- `inventory=fit|near|all`: compute fit ratio for logged-in user if auth exists.
- `favorite=true`: filter after favorites service exists; for now return all until Task 3.

- [ ] **Step 5: Run tests**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_recipe_checker.py tests/test_decision.py tests/test_meals_inventory.py
```

Expected: PASS.

---

## Task 3: Database-Backed Favorites

**Files:**
- Modify: `app/models/__init__.py`
- Create: `app/services/favorites.py`
- Create: `app/routers/favorites.py`
- Modify: `app/main.py`
- Modify: `app/routers/decision.py`
- Test: `tests/test_favorites.py`

- [ ] **Step 1: Write failing favorite tests**

Create `tests/test_favorites.py`:

```python
import time

import pytest
from app.core.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="session")


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
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_favorites.py
```

Expected: FAIL because favorite model/router does not exist.

- [ ] **Step 3: Add model**

In `app/models/__init__.py`, add `RecipeFavorite` with fields from the spec and a uniqueness constraint on `(user_id, target_type, target_id)`.

- [ ] **Step 4: Implement service and router**

Service behavior:

- `add_favorite`: idempotent upsert style. If row exists, update snapshot and return existing row.
- `list_favorites`: newest first.
- `delete_favorite`: user-scoped deletion.
- `favorite_status`: true/false.

Router:

- `GET /v1/favorites`
- `POST /v1/favorites`
- `DELETE /v1/favorites`
- `GET /v1/favorites/status`

- [ ] **Step 5: Integrate favorite filter into recipes**

When `GET /v1/recipes?favorite=true` is called with user auth, return recipes whose ids are in favorites. If not logged in, return empty list or a clear auth error; choose auth error if using `get_current_user`.

- [ ] **Step 6: Run tests**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_favorites.py tests/test_decision.py
```

Expected: PASS.

---

## Task 4: Community MVP

**Files:**
- Modify: `app/models/__init__.py`
- Create: `app/services/community.py`
- Create: `app/routers/community.py`
- Modify: `app/main.py`
- Test: `tests/test_community.py`

- [ ] **Step 1: Write failing community tests**

Create `tests/test_community.py`:

```python
import time

import pytest
from app.core.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="session")


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
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_community.py
```

Expected: FAIL because community router/model does not exist.

- [ ] **Step 3: Add community models**

Add `CommunityPost`, `CommunityComment`, `CommunityLike` to `app/models/__init__.py`. Enforce unique like per user/post.

- [ ] **Step 4: Implement service rules**

Rules:

- Categories allowed: `recipe`, `health`, `checkin`.
- Recipe posts must have non-empty `recipe_payload.title` and `recipe_payload.ingredients`.
- Health/checkin posts can have no `recipe_payload`.
- Empty title/content rejected.
- Like is idempotent.
- Delete is author-only.
- Comments are auth-required.

- [ ] **Step 5: Implement router and register it**

Add endpoints listed in the spec. Include `main.py` router registration.

- [ ] **Step 6: Run tests**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_community.py tests/test_favorites.py tests/test_recipe_checker.py
```

Expected: PASS.

---

## Task 5: Community Recipes In Checker And Favorites

**Files:**
- Modify: `app/services/recipe_checker.py`
- Modify: `app/services/favorites.py`
- Modify: `app/services/community.py`
- Test: `tests/test_community_recipe_flow.py`

- [ ] **Step 1: Write failing integration test**

Create `tests/test_community_recipe_flow.py`:

```python
import time

import pytest
from app.core.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="session")


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
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_community_recipe_flow.py
```

Expected: FAIL until checker supports `community_post`.

- [ ] **Step 3: Support community recipe lookup**

Add community post loading to checker service. Use `recipe_payload` as the recipe snapshot.

- [ ] **Step 4: Preserve snapshots**

Make favorites store enough snapshot fields for community posts:

- `title`
- `category`
- `recipe_payload`
- `images`
- `author_name` if available

- [ ] **Step 5: Run integration tests**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_community_recipe_flow.py tests/test_community.py tests/test_favorites.py tests/test_recipe_checker.py
```

Expected: PASS.

---

## Task 6: Agent Tool Upgrade

**Files:**
- Modify: `app/agent/tools.py`
- Modify: `app/agent/planner.py`
- Modify: `app/services/langgraph_agent.py` or active runtime if planner uses another path
- Test: `tests/test_agent_tools_inventory_favorites.py`

- [ ] **Step 1: Write failing Agent tool test**

Create `tests/test_agent_tools_inventory_favorites.py`:

```python
import time

import pytest
from app.core.database import Base, engine

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _login(client):
    openid = f"agent_tool_user_{int(time.time() * 1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": openid})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['data']['token']}"}


async def test_agent_can_answer_favorite_recipe_inventory_question(client):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    headers = await _login(client)

    recipes = await client.get("/v1/recipes")
    recipe = recipes.json()["data"]["recipes"][0]
    await client.post("/v1/favorites", headers=headers, json={
        "target_type": "system_recipe",
        "target_id": recipe["recipe_id"],
        "snapshot": recipe,
    })

    resp = await client.post("/v1/agent/execute", headers=headers, json={
        "input": "我收藏的菜现在库存能不能做？缺什么？",
        "mode": "full",
        "conversation_id": "agent_tool_test",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    text = data.get("reply", "") + " ".join(str(e) for e in data.get("events", []))
    assert "收藏" in text or "库存" in text or "缺" in text
    assert data.get("degraded") in (True, False, None)
```

- [ ] **Step 2: Run test and verify it fails or lacks tool evidence**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_agent_tools_inventory_favorites.py
```

Expected: FAIL or response does not mention inventory/favorites until tool routing exists.

- [ ] **Step 3: Add tool functions**

Add functions wrapping existing services:

- `tool_list_favorites`
- `tool_current_inventory`
- `tool_check_recipe`
- `tool_search_recipes`

- [ ] **Step 4: Planner routing**

When input contains any of:

- `收藏`
- `库存`
- `缺什么`
- `能不能做`
- `已有食材`

Planner should schedule favorites/inventory/checker tools before generic recommendation.

- [ ] **Step 5: Run Agent tests**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_agent.py tests/test_agent_runtime.py tests/test_langgraph_agent.py tests/test_agent_tools_inventory_favorites.py
```

Expected: PASS.

---

## Task 7: Frontend API Layer

**Files:**
- Modify: `bsapp/src/api/index.js`

- [ ] **Step 1: Add ApiService methods**

Add methods:

```javascript
async addInventoryItem(item) {}
async updateInventoryItem(itemId, item) {}
async deleteInventoryItem(itemId) {}
async getInventoryStats() {}
async checkRecipe(targetType, targetId) {}
async getFavorites() {}
async addFavorite(targetType, targetId, snapshot) {}
async removeFavorite(targetType, targetId) {}
async getFavoriteStatus(targetType, targetId) {}
async getCommunityPosts(category = 'all') {}
async createCommunityPost(payload) {}
async getCommunityPost(postId) {}
async likeCommunityPost(postId) {}
async unlikeCommunityPost(postId) {}
async getCommunityComments(postId) {}
async addCommunityComment(postId, content) {}
```

- [ ] **Step 2: Keep old API compatibility**

Do not remove existing methods used by home, recognition, guide, nutrition, quality, list export.

- [ ] **Step 3: Build**

Run:

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

Expected: PASS.

---

## Task 8: Frontend Navigation And Pages

**Files:**
- Modify: `bsapp/src/pages.json`
- Create: `bsapp/src/pages/inventory/inventory.vue`
- Create: `bsapp/src/pages/favorites/favorites.vue`
- Create: `bsapp/src/pages/recipe-checker/recipe-checker.vue`
- Create: `bsapp/src/pages/community/community.vue`
- Create: `bsapp/src/pages/community-detail/community-detail.vue`
- Create: `bsapp/src/pages/community-publish/community-publish.vue`
- Modify: `bsapp/src/pages/profile/profile.vue`
- Modify: `bsapp/src/pages/home/home.vue`

- [ ] **Step 1: Update tabBar**

Set tabBar:

- 首页 -> `pages/home/home`
- 识别 -> `pages/ingredient-recognition/ingredient-recognition`
- 菜谱 -> `pages/explore/explore`
- 社区 -> `pages/community/community`
- 我的 -> `pages/profile/profile`

Keep `pages/food-knowledge/food-knowledge` in `pages` but no longer as a tab.

- [ ] **Step 2: Add simple page shells**

Each new page must load data from backend and show empty/error states:

- Inventory page: current inventory, add/edit/delete buttons.
- Favorites page: favorite list, check/plan actions.
- Recipe checker page: owned/missing/shopping list/check ratio.
- Community feed: categories and post cards.
- Community detail: post content, comments, like/favorite.
- Community publish: category, title, content, image list placeholder, structured recipe fields for recipe category.

- [ ] **Step 3: Add entries in profile and home**

Profile page entries:

- 我的收藏
- 我的发布
- 库存管理

Home quick entries:

- 库存
- 菜谱库
- 社区

- [ ] **Step 4: Build**

Run:

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

Expected: PASS.

---

## Task 9: Frontend Recipe Library And Recipe Actions

**Files:**
- Modify: `bsapp/src/pages/explore/explore.vue`
- Modify: `bsapp/src/pages/recipe-detail/recipe-detail.vue`
- Modify: `bsapp/src/components/recipe-card.vue`
- Create: `bsapp/src/components/favorite-button.vue`
- Create: `bsapp/src/components/recipe-check-panel.vue`

- [ ] **Step 1: Add favorite component**

Component behavior:

- Props: `targetType`, `targetId`, `snapshot`.
- On mount, call favorite status.
- Tap toggles backend favorite.
- Emits `change`.
- Shows text/icon state without relying on missing SVG.

- [ ] **Step 2: Upgrade Explore to 菜谱库**

Add filters:

- 全部
- 当前库存可做
- 缺少少量食材
- 我的收藏
- 社区菜谱
- 快手
- 高蛋白

Search should call backend or filter full loaded list if API returns enough fields.

- [ ] **Step 3: Add checker entry**

Every recipe card action:

- 收藏
- 清点
- 加入计划

`清点` navigates to `/pages/recipe-checker/recipe-checker?targetType=system_recipe&targetId=...`.

- [ ] **Step 4: Recipe detail real actions**

Replace local fake like with backend favorite.

Add:

- 清点食材
- 缺少项加入购物清单
- 加入今日计划

- [ ] **Step 5: Build and smoke**

Run:

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

Then open local H5 and check navigation manually.

---

## Task 10: Frontend Community

**Files:**
- Modify: `bsapp/src/pages/community/community.vue`
- Modify: `bsapp/src/pages/community-detail/community-detail.vue`
- Modify: `bsapp/src/pages/community-publish/community-publish.vue`
- Create: `bsapp/src/components/community-post-card.vue`

- [ ] **Step 1: Feed page**

Show category tabs:

- 全部
- 菜谱分享
- 健康咨询
- 饮食打卡

Each card shows title, content preview, image count, like/comment counts, favorite action if recipe payload exists, and “导入清单/清点” only for recipe posts.

- [ ] **Step 2: Publish page**

For category `recipe`, require:

- title
- content
- at least one ingredient row

For `health` and `checkin`, allow no recipe payload.

- [ ] **Step 3: Detail page**

Support:

- Like/unlike
- Comment list
- Add comment
- Favorite if recipe post
- Check/import recipe if recipe post
- Health disclaimer for health category

- [ ] **Step 4: Build**

Run:

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

Expected: PASS.

---

## Task 11: Verification And Demo Refresh

**Files:**
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/ByteSavor_项目总流程与答辩说明.md`
- Create: `docs/ByteSavor_社区收藏库存扩展测试文档_2026-06-15.md`

- [ ] **Step 1: Run backend regression**

Run:

```bash
JWT_SECRET=test-review-secret /Users/liwenbin930/Desktop/bytesavor-backend/venv/bin/python -m pytest -q tests/test_auth.py tests/test_decision.py tests/test_meals_inventory.py tests/test_feedback_memory.py tests/test_food_guide.py tests/test_inventory_stats.py tests/test_recipe_checker.py tests/test_favorites.py tests/test_community.py tests/test_community_recipe_flow.py tests/test_agent_tools_inventory_favorites.py
```

Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd /Users/liwenbin930/Desktop/bytesavor-backend/bsapp
npm run build:h5
```

Expected: PASS.

- [ ] **Step 3: Browser smoke**

Start backend and frontend if not running.

Check:

- New user has empty inventory/favorites/community personal state.
- Manual add inventory works.
- Recipe library can search and check missing ingredients.
- Favorite persists across refresh.
- Community recipe can be posted by one user and favorited by another.
- Community recipe can enter checker.
- Add plan does not count nutrition.
- Complete meal counts nutrition and deducts inventory.
- Rating feedback still appears.

- [ ] **Step 4: Update docs**

Update docs with:

- New feature flow.
- New API list.
- New tests and role demo mapping.
- Remaining risks: unit conversion, image storage, moderation, production auth, medical advice boundary.

---

## Subagent Execution Split

Use disjoint write scopes:

1. Backend Inventory/Checker Agent
   - Tasks 1 and 2.
   - Write scope: inventory service/router, recipe checker/router, related tests.

2. Backend Favorites/Community Agent
   - Tasks 3, 4 and 5.
   - Write scope: models additions, favorites/community services/routers/tests.

3. Agent Tools Agent
   - Task 6.
   - Write scope: agent tools/planner/runtime tests.
   - Should start after Tasks 1-5 APIs exist.

4. Frontend Navigation/Core Pages Agent
   - Tasks 7 and 8.
   - Write scope: `api/index.js`, `pages.json`, new page shells, home/profile entries.

5. Frontend Recipe/Community UX Agent
   - Tasks 9 and 10.
   - Write scope: explore, recipe detail, favorite/check components, community pages.
   - Should start after API method names are stable.

6. Verification/Docs Agent
   - Task 11.
   - Write scope: docs only and test reports.
   - Should run after implementation agents finish.

## Self-Review

- Spec coverage: community, favorites, recipe checker, inventory management, Agent tool upgrade, UI navigation, tests and docs are covered.
- Placeholder scan: no TBD/TODO placeholders are left.
- Type consistency: uses `target_type`, `target_id`, `system_recipe`, `community_post` consistently.
- Scope check: this is a large multi-subsystem plan. The recommended execution is staged; do not implement all pages before backend contracts pass tests.
- Main risk: concurrent subagents touching `app/models/__init__.py`, `app/main.py`, `bsapp/src/api/index.js`, and `pages.json` must be integrated carefully by the lead agent.

