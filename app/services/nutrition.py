from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe


async def calc_gap(db: AsyncSession, recipe_ids: list[str], goal: str = "") -> dict:
    if not recipe_ids:
        return {}

    r = await db.execute(select(Recipe).where(Recipe.id.in_(recipe_ids)))
    recipes = r.scalars().all()

    total = {"protein": 0, "carbs": 0, "fat": 0, "calories": 0}
    for rec in recipes:
        total["protein"] += rec.protein
        total["carbs"] += rec.carbs
        total["fat"] += rec.fat
        total["calories"] += rec.calories

    targets = _target_for_goal(goal)
    gaps = {}
    for k in ["protein", "carbs", "fat"]:
        if total[k] < targets[k] * 0.7:
            gaps[k] = "still_needed"
        elif total[k] > targets[k] * 1.3:
            gaps[k] = "exceeded"
    return gaps


def _target_for_goal(goal: str) -> dict:
    if goal == "fat_loss":
        return {"protein": 80, "carbs": 50, "fat": 30}
    if goal == "muscle_gain":
        return {"protein": 120, "carbs": 100, "fat": 50}
    return {"protein": 70, "carbs": 80, "fat": 45}  # balanced
