FOOD_ANALYSIS = """你是一个专业营养师。仔细看这张图，列出所有识别到的食材，判断新鲜度和性状，并逐个估算分量。以 JSON 格式返回：

{
  "ingredients": [
    {
      "name": "食材名",
      "confidence": 0.95,
      "freshness": "high",
      "state": "新鲜",
      "features": "外观特征描述(如颜色、纹理、饱满度)",
      "weight_estimate": 250
    }
  ],
  "portion_estimation": {"total_weight": 所有食材估算总克数}
}

freshness: high/medium/low
state: 新鲜/冷藏/冷冻/干货/腌制
weight_estimate: 该食材估算克数(整数)
total_weight: 所有食材估算重量总和(整数)"""

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
