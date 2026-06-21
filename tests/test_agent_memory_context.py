"""测试 MemoryContext 组装和 memory_used 生成。"""
import pytest
from app.services.agent_memory import build_memory_used


def test_memory_context_empty_for_anonymous():
    """未登录时 build_memory_context 返回安全空结构。"""
    # 不依赖 DB，测试 build_memory_used 在空 context 下行为
    empty_ctx = {
        "conversation_memory": {"last_ingredients": [], "last_recipes": [], "last_user_goal": ""},
        "preference_memory": {"liked_tags": [], "avoid_tags": [], "liked_ingredients": [], "avoid_ingredients": []},
        "fact_memory": {"inventory": [], "today_nutrition_gap": {}, "planned_meals": []},
        "correction_memory": {"recent_aliases": []},
    }
    used = build_memory_used(empty_ctx)
    assert isinstance(used, list)
    assert len(used) == 0  # 空上下文不产生 memory_used


def test_memory_used_format():
    """memory_used 每条包含 type, key, summary 三个字段。"""
    ctx = {
        "conversation_memory": {
            "last_ingredients": ["牛肉", "南瓜"],
            "last_recipes": ["南瓜牛肉饭"],
            "last_user_goal": "fat_loss",
        },
        "preference_memory": {
            "liked_tags": ["high_protein", "light"],
            "avoid_tags": ["oily"],
            "liked_ingredients": ["牛肉"],
            "avoid_ingredients": [],
        },
        "fact_memory": {
            "inventory": [{"name": "南瓜", "amount": 300, "unit": "g"}],
            "today_nutrition_gap": {"calories": 800, "protein": 45},
            "planned_meals": [],
        },
        "correction_memory": {
            "recent_aliases": [],
        },
    }
    used = build_memory_used(ctx)
    assert len(used) >= 4

    for item in used:
        assert "type" in item, f"Missing 'type' in {item}"
        assert "key" in item, f"Missing 'key' in {item}"
        assert "summary" in item, f"Missing 'summary' in {item}"
        assert item["type"] in ("conversation", "preference", "fact", "correction")
        assert isinstance(item["summary"], str)
        assert len(item["summary"]) > 0

    # 验证具体条目
    types = [i["type"] for i in used]
    assert "conversation" in types
    assert "preference" in types
    assert "fact" in types


def test_memory_used_conversation_ingredients():
    """会话记忆包含食材时应生成对应 summary。"""
    ctx = {
        "conversation_memory": {"last_ingredients": ["牛肉"], "last_recipes": [], "last_user_goal": ""},
        "preference_memory": {"liked_tags": [], "avoid_tags": [], "liked_ingredients": [], "avoid_ingredients": []},
        "fact_memory": {"inventory": [], "today_nutrition_gap": {}, "planned_meals": []},
        "correction_memory": {"recent_aliases": []},
    }
    used = build_memory_used(ctx)
    conv_items = [i for i in used if i["type"] == "conversation"]
    assert len(conv_items) == 1
    assert "牛肉" in conv_items[0]["summary"]
    assert conv_items[0]["key"] == "last_ingredients"


def test_memory_used_health_goal():
    """非 balanced 目标应生成 health_goal 条目。"""
    ctx = {
        "conversation_memory": {"last_ingredients": [], "last_recipes": [], "last_user_goal": "fat_loss"},
        "preference_memory": {"liked_tags": [], "avoid_tags": [], "liked_ingredients": [], "avoid_ingredients": []},
        "fact_memory": {"inventory": [], "today_nutrition_gap": {}, "planned_meals": []},
        "correction_memory": {"recent_aliases": []},
    }
    used = build_memory_used(ctx)
    goal_items = [i for i in used if i["key"] == "health_goal"]
    assert len(goal_items) == 1
    assert "减脂" in goal_items[0]["summary"]


def test_memory_used_avoid_tags():
    """避开口味应生成对应条目。"""
    ctx = {
        "conversation_memory": {"last_ingredients": [], "last_recipes": [], "last_user_goal": ""},
        "preference_memory": {"liked_tags": [], "avoid_tags": ["oily"], "liked_ingredients": [], "avoid_ingredients": []},
        "fact_memory": {"inventory": [], "today_nutrition_gap": {}, "planned_meals": []},
        "correction_memory": {"recent_aliases": []},
    }
    used = build_memory_used(ctx)
    avoid_items = [i for i in used if i["key"] == "avoid_tags"]
    assert len(avoid_items) == 1
    assert "oily" in avoid_items[0]["summary"]


def test_memory_used_inventory():
    """有库存时应生成 available_items 条目。"""
    ctx = {
        "conversation_memory": {"last_ingredients": [], "last_recipes": [], "last_user_goal": ""},
        "preference_memory": {"liked_tags": [], "avoid_tags": [], "liked_ingredients": [], "avoid_ingredients": []},
        "fact_memory": {"inventory": [{"name": "鸡蛋"}, {"name": "番茄"}], "today_nutrition_gap": {}, "planned_meals": []},
        "correction_memory": {"recent_aliases": []},
    }
    used = build_memory_used(ctx)
    inv_items = [i for i in used if i["key"] == "available_items"]
    assert len(inv_items) == 1
    assert "2" in inv_items[0]["summary"]


def test_memory_used_correction_aliases():
    """有纠错别名时应生成对应条目。"""
    ctx = {
        "conversation_memory": {"last_ingredients": [], "last_recipes": [], "last_user_goal": ""},
        "preference_memory": {"liked_tags": [], "avoid_tags": [], "liked_ingredients": [], "avoid_ingredients": []},
        "fact_memory": {"inventory": [], "today_nutrition_gap": {}, "planned_meals": []},
        "correction_memory": {"recent_aliases": [{"from": "西红柿", "to": "番茄"}]},
    }
    used = build_memory_used(ctx)
    corr_items = [i for i in used if i["type"] == "correction"]
    assert len(corr_items) == 1
    assert "1" in corr_items[0]["summary"]
