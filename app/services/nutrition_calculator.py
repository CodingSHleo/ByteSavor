"""
食物营养成分数据库 + 按重量计算营养素。
数据来源：中国食物成分表，每 100g 可食部。
"""
from __future__ import annotations

# 每 100g 食物的营养素：{calories(kcal), protein(g), carbs(g), fat(g), fiber(g)}
FOOD_NUTRITION: dict[str, dict[str, float]] = {
    # 水果
    "西瓜": {"calories": 32, "protein": 0.6, "carbs": 7.6, "fat": 0.2, "fiber": 0.3},
    "苹果": {"calories": 53, "protein": 0.2, "carbs": 13.5, "fat": 0.2, "fiber": 1.2},
    "香蕉": {"calories": 93, "protein": 1.4, "carbs": 22.8, "fat": 0.2, "fiber": 1.2},
    "橙子": {"calories": 48, "protein": 0.8, "carbs": 11.1, "fat": 0.2, "fiber": 0.6},
    "葡萄": {"calories": 44, "protein": 0.5, "carbs": 10.3, "fat": 0.2, "fiber": 0.4},
    "草莓": {"calories": 32, "protein": 1.0, "carbs": 7.1, "fat": 0.2, "fiber": 1.1},
    "梨": {"calories": 51, "protein": 0.4, "carbs": 13.1, "fat": 0.1, "fiber": 2.0},
    # 蔬菜
    "西红柿": {"calories": 20, "protein": 0.9, "carbs": 4.0, "fat": 0.2, "fiber": 0.5},
    "黄瓜": {"calories": 16, "protein": 0.8, "carbs": 2.9, "fat": 0.2, "fiber": 0.5},
    "白菜": {"calories": 17, "protein": 1.5, "carbs": 2.4, "fat": 0.2, "fiber": 0.8},
    "小白菜": {"calories": 17, "protein": 1.5, "carbs": 2.4, "fat": 0.2, "fiber": 0.8},
    "菠菜": {"calories": 24, "protein": 2.6, "carbs": 2.8, "fat": 0.4, "fiber": 1.7},
    "生菜": {"calories": 15, "protein": 1.4, "carbs": 2.0, "fat": 0.2, "fiber": 1.3},
    "胡萝卜": {"calories": 39, "protein": 1.0, "carbs": 8.8, "fat": 0.2, "fiber": 1.1},
    "白萝卜": {"calories": 21, "protein": 0.9, "carbs": 4.2, "fat": 0.1, "fiber": 0.6},
    "西兰花": {"calories": 36, "protein": 4.1, "carbs": 4.0, "fat": 0.6, "fiber": 1.6},
    "花菜": {"calories": 24, "protein": 2.1, "carbs": 3.4, "fat": 0.2, "fiber": 1.2},
    "南瓜": {"calories": 22, "protein": 0.7, "carbs": 5.3, "fat": 0.1, "fiber": 0.8},
    "冬瓜": {"calories": 12, "protein": 0.4, "carbs": 2.6, "fat": 0.1, "fiber": 0.7},
    "茄子": {"calories": 23, "protein": 1.1, "carbs": 4.5, "fat": 0.2, "fiber": 1.3},
    "青辣椒": {"calories": 23, "protein": 1.4, "carbs": 3.7, "fat": 0.3, "fiber": 2.1},
    "红辣椒": {"calories": 38, "protein": 1.3, "carbs": 8.3, "fat": 0.3, "fiber": 1.4},
    "洋葱": {"calories": 40, "protein": 1.1, "carbs": 9.1, "fat": 0.1, "fiber": 1.3},
    "大蒜": {"calories": 137, "protein": 4.7, "carbs": 27.0, "fat": 0.2, "fiber": 1.3},
    "生姜": {"calories": 46, "protein": 1.3, "carbs": 9.6, "fat": 0.3, "fiber": 1.6},
    "大葱": {"calories": 33, "protein": 1.7, "carbs": 6.5, "fat": 0.3, "fiber": 1.3},
    "香葱": {"calories": 27, "protein": 1.6, "carbs": 4.4, "fat": 0.3, "fiber": 0.9},
    "马铃薯": {"calories": 81, "protein": 2.0, "carbs": 17.8, "fat": 0.2, "fiber": 0.7},
    "菜豆": {"calories": 33, "protein": 2.1, "carbs": 4.9, "fat": 0.2, "fiber": 1.6},
    "长豆角": {"calories": 32, "protein": 2.7, "carbs": 4.1, "fat": 0.2, "fiber": 1.7},
    "卷心菜": {"calories": 24, "protein": 1.5, "carbs": 4.2, "fat": 0.2, "fiber": 1.0},
    "香菇": {"calories": 26, "protein": 2.2, "carbs": 1.9, "fat": 0.3, "fiber": 3.3},
    "蘑菇": {"calories": 24, "protein": 2.7, "carbs": 2.0, "fat": 0.1, "fiber": 2.1},
    # 肉类
    "猪肉": {"calories": 395, "protein": 13.2, "carbs": 2.4, "fat": 37.0, "fiber": 0},
    "牛肉": {"calories": 125, "protein": 20.2, "carbs": 1.2, "fat": 4.2, "fiber": 0},
    "鸡肉": {"calories": 167, "protein": 19.3, "carbs": 1.3, "fat": 9.4, "fiber": 0},
    "鸭肉": {"calories": 240, "protein": 15.5, "carbs": 0.5, "fat": 19.7, "fiber": 0},
    "羊肉": {"calories": 203, "protein": 19.0, "carbs": 0, "fat": 14.1, "fiber": 0},
    "猪排骨": {"calories": 264, "protein": 18.3, "carbs": 0, "fat": 20.4, "fiber": 0},
    # 水产
    "鱼": {"calories": 104, "protein": 17.6, "carbs": 0, "fat": 3.4, "fiber": 0},
    "虾": {"calories": 93, "protein": 18.6, "carbs": 2.8, "fat": 0.8, "fiber": 0},
    "三文鱼": {"calories": 139, "protein": 17.2, "carbs": 0, "fat": 7.8, "fiber": 0},
    "蟹": {"calories": 95, "protein": 13.8, "carbs": 2.3, "fat": 2.3, "fiber": 0},
    # 蛋奶
    "鸡蛋": {"calories": 144, "protein": 13.3, "carbs": 2.8, "fat": 8.8, "fiber": 0},
    "鸭蛋": {"calories": 180, "protein": 12.6, "carbs": 3.1, "fat": 13.0, "fiber": 0},
    "牛奶": {"calories": 54, "protein": 3.0, "carbs": 3.4, "fat": 3.2, "fiber": 0},
    # 主食
    "米饭": {"calories": 116, "protein": 2.6, "carbs": 25.9, "fat": 0.3, "fiber": 0.3},
    "面条": {"calories": 284, "protein": 8.3, "carbs": 61.9, "fat": 0.7, "fiber": 0},
    "馒头": {"calories": 223, "protein": 7.0, "carbs": 44.2, "fat": 1.1, "fiber": 0},
    "面包": {"calories": 313, "protein": 8.3, "carbs": 58.6, "fat": 5.1, "fiber": 0},
    "红薯": {"calories": 61, "protein": 1.1, "carbs": 13.4, "fat": 0.2, "fiber": 1.6},
    "玉米": {"calories": 112, "protein": 4.0, "carbs": 22.8, "fat": 1.2, "fiber": 2.9},
    # 豆制品
    "豆腐": {"calories": 82, "protein": 8.1, "carbs": 3.8, "fat": 3.7, "fiber": 0.1},
    # 调料
    "食用油": {"calories": 899, "protein": 0, "carbs": 0, "fat": 99.9, "fiber": 0},
    "酱油": {"calories": 63, "protein": 5.6, "carbs": 10.1, "fat": 0.1, "fiber": 0},
}

# 默认营养素（未知食物用）
DEFAULT_NUTRITION = {"calories": 80, "protein": 2.0, "carbs": 10.0, "fat": 3.0, "fiber": 0.5}


def get_nutrition(ingredient_name: str) -> dict[str, float]:
    """根据食材名查询每 100g 营养素。未知食材返回默认值。"""
    name = str(ingredient_name or "").strip()
    if name in FOOD_NUTRITION:
        return dict(FOOD_NUTRITION[name])
    # 模糊匹配
    for key, val in FOOD_NUTRITION.items():
        if key in name or name in key:
            return dict(val)
    return dict(DEFAULT_NUTRITION)


def calculate_per_ingredient(ingredient: dict) -> dict:
    """计算单个食材的营养素。按 weight_estimate 折算。
    返回 {name, weight_g, calories, protein, carbs, fat, fiber, per_100g}
    """
    name = ingredient.get("name", "未知")
    weight = ingredient.get("weight_estimate") or ingredient.get("weight", 0)
    if isinstance(weight, str):
        try:
            weight = float(weight)
        except (ValueError, TypeError):
            weight = 0
    weight = max(weight, 1)  # 至少 1g

    per_100g = get_nutrition(name)
    ratio = weight / 100
    return {
        "name": name,
        "weight_g": round(weight),
        "calories": round(per_100g["calories"] * ratio),
        "protein": round(per_100g["protein"] * ratio, 1),
        "carbs": round(per_100g["carbs"] * ratio, 1),
        "fat": round(per_100g["fat"] * ratio, 1),
        "fiber": round(per_100g.get("fiber", 0) * ratio, 1),
        "per_100g": per_100g,
    }


def calculate_total(ingredients: list[dict]) -> dict:
    """计算一批食材的总营养素。
    返回 {total_nutrition, items, item_count, has_unknown}
    """
    items = [calculate_per_ingredient(i) for i in ingredients if isinstance(i, dict)]
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    has_unknown = False
    for item in items:
        for k in total:
            total[k] += item.get(k, 0)
        if item.get("per_100g") == DEFAULT_NUTRITION:
            has_unknown = True
    return {
        "total_nutrition": {k: round(v, 1) for k, v in total.items()},
        "items": items,
        "item_count": len(items),
        "has_unknown": has_unknown,
    }


def calculate_daily_gap(
    total_nutrition: dict[str, float],
    daily_targets: dict[str, float] | None = None,
) -> dict[str, float]:
    """计算摄入后今日剩余缺口。daily_targets 不传则用默认值（2000kcal 日需）。"""
    targets = daily_targets or {"calories": 2000, "protein": 60, "carbs": 250, "fat": 65}
    return {
        k: round(targets.get(k, 0) - total_nutrition.get(k, 0), 1)
        for k in ["calories", "protein", "carbs", "fat"]
    }
