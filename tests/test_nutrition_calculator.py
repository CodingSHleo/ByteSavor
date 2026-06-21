"""测试营养计量：按 weight_estimate 计算单项营养素。"""
from app.services.nutrition_calculator import (
    get_nutrition, calculate_per_ingredient, calculate_total, calculate_daily_gap,
    FOOD_NUTRITION, DEFAULT_NUTRITION,
)


def test_nutrition_watermelon():
    """西瓜 500g → 约 160kcal。"""
    item = calculate_per_ingredient({"name": "西瓜", "weight_estimate": 500})
    assert item["calories"] > 0, "西瓜应有非 0 热量"
    assert item["calories"] == 160  # 500g * 32/100 = 160
    assert item["weight_g"] == 500


def test_nutrition_egg():
    """鸡蛋 100g → 144kcal, 13.3g 蛋白。"""
    item = calculate_per_ingredient({"name": "鸡蛋", "weight_estimate": 100})
    assert item["calories"] == 144
    assert item["protein"] == 13.3


def test_nutrition_rice():
    """米饭 200g → 232kcal。"""
    item = calculate_per_ingredient({"name": "米饭", "weight_estimate": 200})
    assert item["calories"] == 232
    assert item["carbs"] > 50


def test_nutrition_unknown_food():
    """未知食物用默认值。"""
    item = calculate_per_ingredient({"name": "不明物质", "weight_estimate": 100})
    assert item["calories"] == DEFAULT_NUTRITION["calories"]
    assert item["per_100g"] == DEFAULT_NUTRITION


def test_nutrition_total():
    """多个食材总营养素。"""
    items = [
        {"name": "鸡蛋", "weight_estimate": 100},
        {"name": "西瓜", "weight_estimate": 500},
    ]
    result = calculate_total(items)
    assert result["item_count"] == 2
    total = result["total_nutrition"]
    assert total["calories"] == 304  # 144 + 160
    assert total["protein"] == 16.3  # 13.3 + 3.0
    assert not result["has_unknown"]


def test_nutrition_total_has_unknown():
    """含未知食材时标记 has_unknown。"""
    items = [
        {"name": "不明物", "weight_estimate": 100},
    ]
    result = calculate_total(items)
    assert result["has_unknown"]


def test_nutrition_daily_gap():
    """计算今日剩余缺口。"""
    total = {"calories": 500, "protein": 30, "carbs": 80, "fat": 20}
    gap = calculate_daily_gap(total)
    assert gap["calories"] == 1500  # 2000 - 500
    assert gap["protein"] == 30     # 60 - 30


def test_nutrition_synonym_match():
    """同义词也能匹配到营养素（西红柿=番茄→西红柿）。"""
    item = calculate_per_ingredient({"name": "西红柿", "weight_estimate": 200})
    assert item["calories"] > 0
    assert item["calories"] == 40  # 200g * 20/100


def test_nutrition_string_weight():
    """weight_estimate 为字符串时可正常解析。"""
    item = calculate_per_ingredient({"name": "鸡蛋", "weight_estimate": "100"})
    assert item["calories"] == 144


def test_nutrition_min_weight():
    """重量为 0 时至少按 1g 计算。"""
    item = calculate_per_ingredient({"name": "鸡蛋", "weight_estimate": 0})
    assert item["weight_g"] == 1
    assert item["calories"] > 0


def test_nutrition_db_coverage():
    """常见食物都有数据。"""
    common = ["米饭", "鸡蛋", "牛肉", "鸡肉", "猪肉", "豆腐", "白菜", "苹果", "香蕉"]
    for food in common:
        assert food in FOOD_NUTRITION, f"Missing {food} in FOOD_NUTRITION"
        data = FOOD_NUTRITION[food]
        for k in ("calories", "protein", "carbs", "fat"):
            assert data.get(k, 0) > 0, f"{food}.{k} should be > 0"
