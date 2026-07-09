import pytest
from types import SimpleNamespace

from app.services.decision import _rank

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


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
        assert "category" in r
        assert "ingredients" in r
        assert isinstance(r["ingredients"], list)
        assert "micro_highlights" in r
        assert "micronutrients" in r


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


async def test_recipe_explore_list_uses_seed_data_with_micronutrients(client):
    resp = await client.get("/v1/recipes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

    recipes = data["data"]["recipes"]
    assert len(recipes) >= 10
    first = recipes[0]
    assert first["recipe_id"].startswith("r_")
    assert first["title"]
    assert first["category"]
    assert isinstance(first["micro_highlights"], list)
    assert len(first["micro_highlights"]) > 0
    assert {"protein", "carbs", "fat"}.issubset(first["macros"].keys())
    assert {"vitamin_c", "iron", "calcium", "fiber"}.issubset(first["micronutrients"].keys())


async def test_rank_prefers_recipes_covering_all_requested_ingredients():
    recipes = [
        SimpleNamespace(
            id="r_beef_celery",
            title="芹菜牛肉",
            cook_time=20,
            difficulty="easy",
            calories=320,
            protein=28,
            carbs=10,
            fat=14,
            tags=["quick", "high_protein"],
            ingredients=[{"name": "牛肉"}, {"name": "芹菜"}],
        ),
        SimpleNamespace(
            id="r_beef_pumpkin",
            title="南瓜炖牛肉",
            cook_time=30,
            difficulty="easy",
            calories=360,
            protein=30,
            carbs=22,
            fat=12,
            tags=["quick", "high_protein"],
            ingredients=[{"name": "黄牛肉"}, {"name": "去皮南瓜"}],
        ),
    ]

    ranked = _rank(recipes, ["牛肉", "南瓜"], "", "fat_loss", [])

    assert ranked[0]["recipe_id"] == "r_beef_pumpkin"
    assert ranked[0]["match_score"] > ranked[1]["match_score"]


async def test_rank_prefers_specific_requested_ingredient_over_generic_partial_match():
    recipes = [
        SimpleNamespace(
            id="r_beef_celery",
            title="芹菜炒牛肉",
            cook_time=20,
            difficulty="easy",
            calories=320,
            protein=28,
            carbs=10,
            fat=14,
            tags=["quick", "high_protein"],
            ingredients=[{"name": "牛肉"}, {"name": "芹菜"}],
        ),
        SimpleNamespace(
            id="r_chive_egg",
            title="韭黄炒鸡蛋",
            cook_time=10,
            difficulty="easy",
            calories=260,
            protein=18,
            carbs=8,
            fat=12,
            tags=["quick"],
            ingredients=[{"name": "韭黄"}, {"name": "鸡蛋"}],
        ),
    ]

    ranked = _rank(recipes, ["牛肉", "韭黄"], "", "fat_loss", [])

    assert ranked[0]["recipe_id"] == "r_chive_egg"
    assert "韭黄" in [i["name"] for i in ranked[0]["ingredients"]]
    assert ranked[0]["_meta"]["missing_ingredients"] == ["牛肉"]


async def test_rank_does_not_treat_partial_coverage_as_full_match():
    recipes = [
        SimpleNamespace(
            id="r_beef_celery",
            title="芹菜炒牛肉",
            cook_time=20,
            difficulty="easy",
            calories=320,
            protein=28,
            carbs=10,
            fat=14,
            tags=["quick", "high_protein", "low_carb"],
            ingredients=[{"name": "牛肉"}, {"name": "芹菜"}],
        ),
        SimpleNamespace(
            id="r_chive_egg",
            title="韭黄炒鸡蛋",
            cook_time=10,
            difficulty="easy",
            calories=260,
            protein=18,
            carbs=8,
            fat=12,
            tags=["quick"],
            ingredients=[{"name": "韭黄"}, {"name": "鸡蛋"}],
        ),
    ]

    ranked = _rank(recipes, ["牛肉", "韭黄"], "", "fat_loss", [])

    assert ranked[0]["recipe_id"] == "r_chive_egg"
    assert ranked[1]["recipe_id"] == "r_beef_celery"


async def test_rank_specific_requested_ingredient_wins_even_when_generic_has_goal_tags():
    recipes = [
        SimpleNamespace(
            id="r_beef_celery",
            title="芹菜炒牛肉",
            cook_time=20,
            difficulty="easy",
            calories=320,
            protein=28,
            carbs=10,
            fat=14,
            tags=["quick", "high_protein", "low_carb"],
            ingredients=[{"name": "牛肉"}, {"name": "芹菜"}, {"name": "干辣椒"}],
        ),
        SimpleNamespace(
            id="r_chive_egg",
            title="韭黄炒鸡蛋",
            cook_time=10,
            difficulty="easy",
            calories=260,
            protein=18,
            carbs=8,
            fat=12,
            tags=["quick"],
            ingredients=[{"name": "韭黄"}, {"name": "鸡蛋"}],
        ),
    ]

    ranked = _rank(recipes, ["牛肉", "韭黄"], "", "fat_loss", [])

    assert ranked[0]["recipe_id"] == "r_chive_egg"
    assert ranked[0]["_meta"]["matched_ingredients"] == ["韭黄"]
    assert ranked[0]["_meta"]["missing_ingredients"] == ["牛肉"]


async def test_rank_uses_user_preferences_when_ingredient_coverage_is_equal():
    recipes = [
        SimpleNamespace(
            id="r_spicy_beef",
            title="香辣牛肉",
            cook_time=20,
            difficulty="easy",
            calories=340,
            protein=30,
            carbs=12,
            fat=15,
            tags=["spicy", "high_protein"],
            ingredients=[{"name": "牛肉"}, {"name": "辣椒"}],
        ),
        SimpleNamespace(
            id="r_light_beef",
            title="清炒牛肉",
            cook_time=18,
            difficulty="easy",
            calories=300,
            protein=29,
            carbs=9,
            fat=10,
            tags=["light", "high_protein"],
            ingredients=[{"name": "牛肉"}, {"name": "西兰花"}],
        ),
    ]

    ranked = _rank(recipes, ["牛肉"], "", "balanced", ["清淡", "少油"])

    assert ranked[0]["recipe_id"] == "r_light_beef"
    assert "preference_matches" in ranked[0]["_meta"]
    assert "light" in ranked[0]["_meta"]["preference_matches"]


async def test_rank_uses_method_and_constraint_preferences_when_coverage_is_equal():
    recipes = [
        SimpleNamespace(
            id="r_stew_beef",
            title="慢炖牛肉",
            cook_time=60,
            difficulty="medium",
            calories=420,
            protein=34,
            carbs=16,
            fat=22,
            tags=["high_protein", "stew"],
            ingredients=[{"name": "牛肉"}, {"name": "胡萝卜"}],
        ),
        SimpleNamespace(
            id="r_stir_beef",
            title="10分钟快炒牛肉",
            cook_time=10,
            difficulty="easy",
            calories=310,
            protein=30,
            carbs=10,
            fat=12,
            tags=["quick", "high_protein", "stir_fry", "low_oil"],
            ingredients=[{"name": "牛肉"}, {"name": "韭黄"}],
        ),
    ]

    ranked = _rank(
        recipes,
        ["牛肉"],
        "",
        "balanced",
        ["stir_fry", "quick_meal", "low_oil"],
        preference_evidence=["喜欢10分钟快炒，少油清淡"],
    )

    assert ranked[0]["recipe_id"] == "r_stir_beef"
    assert "stir_fry" in ranked[0]["_meta"]["preference_matches"]
    assert "quick_meal" in ranked[0]["_meta"]["preference_matches"]
    assert ranked[0]["_meta"]["preference_evidence"] == ["喜欢10分钟快炒，少油清淡"]


async def test_rank_prefers_tomato_beef_full_match_over_previous_pepper_beef():
    recipes = [
        SimpleNamespace(
            id="r_oyster_pepper_beef",
            title="蚝油青椒牛肉",
            cook_time=20,
            difficulty="easy",
            calories=330,
            protein=30,
            carbs=12,
            fat=14,
            tags=["quick", "high_protein", "low_carb"],
            ingredients=[{"name": "牛肉"}, {"name": "青椒"}, {"name": "蚝油"}],
        ),
        SimpleNamespace(
            id="r_tomato_beef",
            title="番茄牛肉",
            cook_time=25,
            difficulty="easy",
            calories=300,
            protein=29,
            carbs=16,
            fat=10,
            tags=["quick", "high_protein", "low_fat"],
            ingredients=[{"name": "番茄"}, {"name": "牛肉"}],
        ),
    ]

    ranked = _rank(recipes, ["番茄", "牛肉"], "", "fat_loss", [])

    assert ranked[0]["recipe_id"] == "r_tomato_beef"
    assert ranked[0]["_meta"]["matched_ingredients"] == ["牛肉", "西红柿"]
    assert ranked[0]["_meta"]["missing_ingredients"] == []
    assert ranked[1]["_meta"]["missing_ingredients"] == ["西红柿"]
