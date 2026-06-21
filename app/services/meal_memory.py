from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MealRecord, NutritionLog
from app.services import inventory as inventory_svc
from app.services.user import calculate_nutrition_targets, get_profile


def _clean_name(name: str) -> str:
    return inventory_svc.clean_name(name)


def _parse_amount(raw) -> tuple[int | None, str]:
    return inventory_svc.parse_amount(raw)


def _nutrition_from_recipe(recipe: dict) -> dict:
    macros = recipe.get("macros") or {}
    micro = recipe.get("micronutrients") or {}
    nutrition = recipe.get("nutrition") or {}
    return {
        "calories": int(recipe.get("calories") or nutrition.get("calories") or 0),
        "protein": int(macros.get("protein") or recipe.get("protein") or nutrition.get("protein") or 0),
        "carbs": int(macros.get("carbs") or recipe.get("carbs") or nutrition.get("carbs") or 0),
        "fat": int(macros.get("fat") or recipe.get("fat") or nutrition.get("fat") or 0),
        "fiber": int(micro.get("fiber") or nutrition.get("fiber") or 0),
        "vitamin_c": int(micro.get("vitamin_c") or nutrition.get("vitamin_c") or 0),
        "iron": float(micro.get("iron") or nutrition.get("iron") or 0),
    }


def _score(totals: dict, targets: dict | None = None) -> int:
    targets = targets or {"calories": 1800, "protein": 70, "carbs": 220, "fat": 60}
    parts = [
        min(100, totals.get("calories", 0) / targets["calories"] * 100) * 0.25,
        min(100, totals.get("protein", 0) / targets["protein"] * 100) * 0.35,
        min(100, totals.get("carbs", 0) / targets["carbs"] * 100) * 0.2,
        min(100, totals.get("fat", 0) / targets["fat"] * 100) * 0.2,
    ]
    return int(round(sum(parts)))


async def import_inventory(db: AsyncSession, user_id: str, items: list[dict], source: str = "manual") -> list[IngredientInventory]:
    return await inventory_svc.import_items(db, user_id, items, source)


async def current_inventory(db: AsyncSession, user_id: str) -> list[dict]:
    return await inventory_svc.current_inventory(db, user_id)


async def plan_meal(
    db: AsyncSession,
    user_id: str,
    meal_slot: str,
    recipe: dict,
    ingredients_used: list[dict] | None = None,
    shopping_list: list[dict] | None = None,
) -> MealRecord:
    meal = MealRecord(
        user_id=user_id,
        meal_slot=meal_slot or "lunch",
        status="planned",
        recipe_id=recipe.get("recipe_id") or recipe.get("recipeId") or "",
        recipe_snapshot=recipe,
        ingredients_used=ingredients_used or recipe.get("ingredients") or [],
        shopping_list=shopping_list or [],
        nutrition=_nutrition_from_recipe(recipe),
    )
    db.add(meal)
    await db.commit()
    await db.refresh(meal)
    return meal


async def today_meals(db: AsyncSession, user_id: str) -> list[dict]:
    start = datetime.combine(date.today(), datetime.min.time())
    result = await db.execute(
        select(MealRecord)
        .where(MealRecord.user_id == user_id, MealRecord.created_at >= start)
        .order_by(MealRecord.created_at.desc())
    )
    return [_meal_dict(row) for row in result.scalars().all()]


async def complete_meal(db: AsyncSession, user_id: str, meal_id: int) -> MealRecord | None:
    result = await db.execute(select(MealRecord).where(MealRecord.id == meal_id, MealRecord.user_id == user_id))
    meal = result.scalar_one_or_none()
    if meal is None:
        return None
    if meal.status != "completed":
        meal.status = "completed"
        meal.completed_at = datetime.now()
        await _deduct_inventory(db, user_id, meal.ingredients_used or [])
        totals = await nutrition_summary(db, user_id, "day")
        db.add(NutritionLog(
            user_id=user_id,
            score=_score(totals["totals"], totals["targets"]),
            deficits=_deficits(totals["totals"], totals["targets"]),
            recorded_at=date.today(),
        ))
    await db.commit()
    await db.refresh(meal)
    return meal


async def cancel_meal(db: AsyncSession, user_id: str, meal_id: int) -> MealRecord | None:
    result = await db.execute(select(MealRecord).where(MealRecord.id == meal_id, MealRecord.user_id == user_id))
    meal = result.scalar_one_or_none()
    if meal is None:
        return None
    meal.status = "cancelled"
    await db.commit()
    await db.refresh(meal)
    return meal


async def change_meal_slot(db: AsyncSession, user_id: str, meal_id: int, new_slot: str) -> MealRecord | None:
    """批次B: 切换用餐计划 slot（早餐→午餐）。"""
    valid_slots = {"breakfast", "lunch", "dinner", "snack", "late_night"}
    if new_slot not in valid_slots:
        return None
    result = await db.execute(select(MealRecord).where(MealRecord.id == meal_id, MealRecord.user_id == user_id))
    meal = result.scalar_one_or_none()
    if meal is None:
        return None
    meal.meal_slot = new_slot
    await db.commit()
    await db.refresh(meal)
    return meal


async def nutrition_summary(db: AsyncSession, user_id: str, range_name: str = "day") -> dict:
    profile = await get_profile(db, user_id)
    targets = (profile or {}).get("computed_targets") or calculate_nutrition_targets("balanced")
    start = date.today()
    if range_name == "week":
        start = start - timedelta(days=6)
    elif range_name == "weeks":
        start = start - timedelta(days=27)
    start_dt = datetime.combine(start, datetime.min.time())
    result = await db.execute(
        select(MealRecord).where(
            MealRecord.user_id == user_id,
            MealRecord.status == "completed",
            MealRecord.completed_at >= start_dt,
        )
    )
    meals = result.scalars().all()
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "vitamin_c": 0, "iron": 0}
    daily: dict[str, dict] = {}
    for meal in meals:
        nutrition = meal.nutrition or {}
        day_key = (meal.completed_at.date() if meal.completed_at else date.today()).isoformat()
        daily.setdefault(day_key, {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "vitamin_c": 0, "iron": 0})
        for key in totals:
            value = nutrition.get(key, 0) or 0
            totals[key] += value
            daily[day_key][key] += value
    return {"range": range_name, "score": _score(totals, targets), "targets": targets, "totals": totals, "daily": daily, "meals": [_meal_dict(m) for m in meals]}


async def _deduct_inventory(db: AsyncSession, user_id: str, used_items: list[dict]) -> None:
    await inventory_svc.deduct_inventory(db, user_id, used_items)


def _deficits(totals: dict, targets: dict | None = None) -> list[str]:
    targets = targets or {"protein": 70, "fiber": 30, "vitamin_c": 90}
    deficits = []
    if totals.get("protein", 0) < targets.get("protein", 70):
        deficits.append("protein")
    if totals.get("fiber", 0) < targets.get("fiber", 30):
        deficits.append("fiber")
    if totals.get("vitamin_c", 0) < targets.get("vitamin_c", 90):
        deficits.append("vitamin_c")
    return deficits


def _inventory_dict(row: IngredientInventory) -> dict:
    return inventory_svc.inventory_dict(row)


def _meal_dict(row: MealRecord) -> dict:
    return {
        "id": row.id,
        "meal_slot": row.meal_slot,
        "status": row.status,
        "recipe_id": row.recipe_id,
        "recipe": row.recipe_snapshot or {},
        "ingredients_used": row.ingredients_used or [],
        "shopping_list": row.shopping_list or [],
        "nutrition": row.nutrition or {},
        "planned_at": row.planned_at.isoformat() if row.planned_at else "",
        "completed_at": row.completed_at.isoformat() if row.completed_at else "",
    }
