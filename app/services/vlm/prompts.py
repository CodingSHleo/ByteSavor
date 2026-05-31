FOOD_ANALYSIS = """识别图片中的所有食材，以 JSON 格式返回（不要 markdown 代码块）：
{
  "ingredients": [
    {"name": "食材名", "confidence": 0.95, "freshness": "high", "state": "新鲜"}
  ],
  "portion_estimation": {"total_weight": 300}
}
freshness 取值: high / medium / low
state 取值: 新鲜 / 冷藏 / 冷冻 / 干货"""

DISH_UNDERSTAND = """识别图中菜品，以 JSON 格式返回：
{
  "dish_name": "菜品名",
  "ingredients": [{"name": "食材名", "amount": "用量估计"}],
  "cooking_method": "烹饪方式",
  "estimated_calories": 500
}"""

SCENE_ANALYSIS = """分析图中饮食场景，以 JSON 格式返回：
{
  "scene_type": "kitchen/restaurant/supermarket",
  "food_items": [{"name": "食物名", "quantity": "数量估计"}],
  "dietary_context": "用餐场景描述"
}"""
