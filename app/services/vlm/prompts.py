FOOD_ANALYSIS_PROMPT_VERSION = "food-analysis-v2-fast"

FOOD_ANALYSIS = """识别图片中的主要食材，只返回 JSON，不要解释。优先列出可用于做菜/摄入记录的食材，最多 12 项。

{
  "ingredients": [
    {
      "name": "食材名",
      "confidence": 0.95,
      "freshness": "high",
      "state": "新鲜",
      "weight_estimate": 250
    }
  ],
  "portion_estimation": {"total_weight": 估算总克数}
}

freshness: high/medium/low
state: 新鲜/冷藏/冷冻/干货/腌制
weight_estimate 和 total_weight 必须是整数。"""

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
