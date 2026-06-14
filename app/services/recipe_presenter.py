from app.models.recipe import Recipe


def category(tags: list[str]) -> str:
    t = {str(x).lower() for x in tags or []}
    if "quick" in t:
        return "quick"
    if "vegetarian" in t:
        return "vegetarian"
    if "fat_loss" in t or "low_carb" in t or "light" in t:
        return "low_fat"
    if "high_protein" in t:
        return "high_protein"
    if "comfort_food" in t:
        return "comfort"
    return "balanced"


def micronutrients(recipe: Recipe) -> dict:
    text = " ".join([i.get("name", "") for i in recipe.ingredients or []])
    fiber = max(2, min(12, int(recipe.carbs * 0.18)))
    vitamin_c = 8
    iron = 1.5
    calcium = 35
    potassium = 260
    folate = 45
    omega3 = 0.1

    if any(x in text for x in ["西兰花", "番茄", "生菜", "黄瓜", "冬瓜", "豆角", "南瓜", "蒜苗"]):
        vitamin_c += 35
        fiber += 3
        potassium += 180
        folate += 35
    if any(x in text for x in ["牛肉", "排骨", "猪", "里脊"]):
        iron += 2.4
    if any(x in text for x in ["鸡胸", "鸡蛋", "豆腐"]):
        iron += 0.8
        calcium += 45
    if any(x in text for x in ["鲈鱼", "鱼", "虾", "紫菜"]):
        omega3 += 0.8
        calcium += 35
    if "豆腐" in text:
        calcium += 120
    if any(x in text for x in ["土豆", "南瓜", "冬瓜"]):
        potassium += 220

    return {
        "fiber": fiber,
        "vitamin_c": vitamin_c,
        "iron": round(iron, 1),
        "calcium": calcium,
        "potassium": potassium,
        "folate": folate,
        "omega3": round(omega3, 1),
    }


def micro_highlights(micro: dict) -> list[str]:
    highlights = []
    if micro.get("vitamin_c", 0) >= 35:
        highlights.append("高维C")
    if micro.get("iron", 0) >= 3:
        highlights.append("补铁")
    if micro.get("calcium", 0) >= 90:
        highlights.append("高钙")
    if micro.get("fiber", 0) >= 5:
        highlights.append("高纤维")
    if micro.get("omega3", 0) >= 0.8:
        highlights.append("Omega-3")
    return highlights or ["营养均衡"]


def recipe_brief(recipe: Recipe) -> dict:
    micro = micronutrients(recipe)
    return {
        "recipe_id": recipe.id,
        "recipeId": recipe.id,
        "title": recipe.title,
        "cook_time": recipe.cook_time,
        "cookTime": recipe.cook_time,
        "difficulty": recipe.difficulty,
        "calories": recipe.calories,
        "ingredients": recipe.ingredients or [],
        "category": category(recipe.tags),
        "tags": recipe.tags or [],
        "macros": {"protein": recipe.protein, "carbs": recipe.carbs, "fat": recipe.fat},
        "micronutrients": micro,
        "micro_highlights": micro_highlights(micro),
    }
