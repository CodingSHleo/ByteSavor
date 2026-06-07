"""食物营养分析 —— VLM识别 + 营养计算 + 个性化建议"""

from app.services.vlm import analyze_food
from app.services.ingredient_tips import get_tip

# 常见食物热量参考（每100g）
CALORIE_DB = {
    "米饭": 116, "白米饭": 116, "糙米饭": 123, "馒头": 223, "面条": 110, "面包": 266,
    "牛肉": 125, "猪肉": 395, "鸡肉": 167, "鸡胸肉": 133, "羊肉": 203, "鸡蛋": 155,
    "鱼": 104, "鲈鱼": 105, "虾": 99, "虾仁": 99, "三文鱼": 208,
    "西兰花": 34, "番茄": 18, "西红柿": 18, "生菜": 13, "黄瓜": 15, "菠菜": 23,
    "土豆": 81, "胡萝卜": 41, "南瓜": 26, "玉米": 112, "豆腐": 76,
    "苹果": 52, "香蕉": 91, "西瓜": 31, "榴莲": 147, "葡萄": 69, "橙子": 47,
}

# 份量参照
PORTION_GUIDE = {
    "一拳": 150, "半拳": 75, "一个": 50, "一把": 30, "一掌心": 100,
    "一拳头大小": 150, "小碗": 200, "中碗": 300, "大碗": 400,
}

# 目标推荐（每日）
DAILY_TARGET = {
    "fat_loss": {"calories": 1800, "protein": 90, "carbs": 150, "fat": 50},
    "muscle_gain": {"calories": 2800, "protein": 140, "carbs": 300, "fat": 75},
    "balanced": {"calories": 2200, "protein": 80, "carbs": 250, "fat": 65},
}

REFERENCE = {
    "主食": "一拳头 ≈ 150g 熟米饭 ≈ 175kcal",
    "蛋白质": "一掌心 ≈ 100g 肉/鱼 ≈ 150kcal",
    "蔬菜": "双手捧 ≈ 200g 蔬菜 ≈ 60kcal",
    "脂肪": "大拇指 ≈ 15g 油/酱料 ≈ 135kcal",
}


def estimate_calories(name: str, weight_g: int = 100) -> dict:
    """根据食材名估算营养"""
    for key, cal in sorted(CALORIE_DB.items(), key=lambda x: -len(x[0])):
        if key in name or name in key:
            protein = round(weight_g * 0.2)
            fat = round(weight_g * 0.05)
            carbs = round(weight_g * 0.15)
            return {"name": name, "weight": weight_g, "calories": round(cal * weight_g / 100),
                    "protein": protein, "carbs": carbs, "fat": fat, "cal_per_100g": cal}
    return {"name": name, "weight": weight_g, "calories": round(weight_g * 1.5),
            "protein": round(weight_g*0.15), "carbs": round(weight_g*0.1), "fat": round(weight_g*0.05), "cal_per_100g": 150}


def portion_reference(weight_g: int) -> str:
    """给出份量参照"""
    if weight_g <= 50: return f"约{weight_g}g，相当于一小口"
    if weight_g <= 100: return f"约{weight_g}g，相当于半拳大小"
    if weight_g <= 200: return f"约{weight_g}g，相当于一拳大小"
    if weight_g <= 400: return f"约{weight_g}g，相当于两拳大小"
    return f"约{weight_g}g，相当于{weight_g//150}拳大小"


async def analyze_meal(image_data: str, goal: str = "balanced") -> dict:
    """分析一顿饭的营养"""
    result = await analyze_food(image_data)
    if not result or not result.get("ingredients"):
        return {"status": "no_food"}

    items = []
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    target = DAILY_TARGET.get(goal, DAILY_TARGET["balanced"])

    for ing in result["ingredients"]:
        wt = ing.get("weight_estimate", 100) or 100
        info = estimate_calories(ing["name"], wt)
        info["freshness"] = ing.get("freshness", "medium")
        info["portion_ref"] = portion_reference(wt)
        items.append(info)
        for k in ["calories", "protein", "carbs", "fat"]:
            total[k] += info[k]

    # 对比目标
    gaps = {}
    for k in ["calories", "protein", "carbs", "fat"]:
        pct = round(total[k] / target[k] * 100)
        gaps[k] = {"current": total[k], "target": target[k], "pct": pct,
                   "advice": "刚好" if 70 <= pct <= 130 else ("还需补充" if pct < 70 else "已超标")}

    return {
        "status": "ok",
        "items": items,
        "total": total,
        "target": target,
        "gaps": gaps,
        "reference": REFERENCE,
        "goal": goal,
    }
