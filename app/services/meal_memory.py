from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngredientInventory, MealRecord, NutritionLog, ShoppingListItem
from app.services import inventory as inventory_svc
from app.services.food_synonyms import normalize_ingredient_name
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


def _ingredient_dict(raw: dict) -> dict | None:
    name = _clean_name(raw.get("name") or raw.get("title") or "")
    amount, unit = _parse_amount(raw.get("amount") or raw.get("display") or raw.get("weight_estimate"))
    if raw.get("unit"):
        unit = str(raw.get("unit") or "").strip()
    if not name:
        return None
    item = {"name": name}
    if amount is not None:
        item["amount"] = amount
    if unit:
        item["unit"] = unit
    return item


def _recipe_ingredients(recipe: dict) -> list[dict]:
    items = recipe.get("ingredients") or recipe.get("ingredient_list") or []
    normalized = []
    for item in items:
        if isinstance(item, dict):
            parsed = _ingredient_dict(item)
        else:
            amount, unit = _parse_amount(item)
            name = str(item or "").replace(str(amount or ""), "").replace(unit, "").strip(" -:：")
            parsed = {"name": _clean_name(name), "amount": amount, "unit": unit} if name else None
        if parsed:
            normalized.append(parsed)
    return normalized


async def _apply_inventory_for_plan(db: AsyncSession, user_id: str, requested: list[dict]) -> dict:
    deductions: list[dict] = []
    shopping_list: list[dict] = []

    for item in requested:
        name = _clean_name(item.get("name"))
        amount, unit = _parse_amount(item.get("amount") or item.get("display"))
        if item.get("unit"):
            unit = str(item.get("unit") or "").strip()
        if not name:
            continue
        if amount is None:
            shopping_list.append({"name": name, "amount": None, "unit": unit or "", "display": item.get("display") or ""})
            continue

        row = await _find_inventory_match(db, user_id, name, unit or "")
        if row and row.amount is not None:
            before = int(row.amount or 0)
            deduct_amount = min(before, amount)
            if deduct_amount > 0:
                row.amount = max(0, before - deduct_amount)
                deductions.append({
                    "name": name,
                    "matched_inventory_name": row.name,
                    "amount": deduct_amount,
                    "unit": unit or "",
                    "before": before,
                    "after": row.amount,
                    "display": f"{deduct_amount}{unit or ''}",
                })
            shortage = amount - deduct_amount
            if shortage > 0:
                shopping_list.append({
                    "name": name,
                    "amount": shortage,
                    "unit": unit or "",
                    "display": f"{shortage}{unit or ''}",
                })
        else:
            shopping_list.append({
                "name": name,
                "amount": amount,
                "unit": unit or "",
                "display": f"{amount}{unit or ''}",
            })

    return {
        "deductions": deductions,
        "shopping_list": shopping_list,
    }


async def _find_inventory_match(db: AsyncSession, user_id: str, name: str, unit: str) -> IngredientInventory | None:
    result = await db.execute(
        select(IngredientInventory).where(
            IngredientInventory.user_id == user_id,
            IngredientInventory.unit == (unit or ""),
        )
    )
    target = normalize_ingredient_name(name)
    rows = list(result.scalars().all())
    for row in rows:
        if row.name == name:
            return row
    for row in rows:
        row_norm = normalize_ingredient_name(row.name)
        if row_norm == target or row_norm in target or target in row_norm:
            return row
    return None


def _adopt_events(meal_slot: str, deductions: list[dict], shopping_list: list[dict]) -> list[dict]:
    return [
        {
            "type": "agent_event",
            "stage": "plan",
            "status": "success",
            "title": "已采纳菜谱",
            "detail": f"已加入{meal_slot or 'lunch'}用餐计划",
            "summary": {"meal_slot": meal_slot or "lunch"},
        },
        {
            "type": "agent_event",
            "stage": "inventory",
            "status": "success" if deductions else "partial",
            "title": "已同步库存",
            "detail": f"扣减 {len(deductions)} 项库存",
            "summary": {"deducted_count": len(deductions)},
        },
        {
            "type": "agent_event",
            "stage": "shopping_list",
            "status": "success" if shopping_list else "skipped",
            "title": "已生成补购清单",
            "detail": f"缺少 {len(shopping_list)} 项食材" if shopping_list else "库存已覆盖主要食材",
            "summary": {"shopping_item_count": len(shopping_list)},
        },
    ]


async def adopt_recipe(
    db: AsyncSession,
    user_id: str,
    meal_slot: str,
    recipe: dict,
) -> dict:
    """Agent 采纳菜谱动作：创建计划、立即同步库存、生成缺货清单。"""
    requested = _recipe_ingredients(recipe)
    inventory_result = await _apply_inventory_for_plan(db, user_id, requested)
    deductions = inventory_result["deductions"]
    shopping_list = inventory_result["shopping_list"]
    recipe_snapshot = {
        **recipe,
        "_agent_action": "adopt_recipe",
        "_agent_inventory_applied": True,
        "_agent_inventory_preview": {"deductions": deductions, "shopping_list": shopping_list},
    }
    meal = MealRecord(
        user_id=user_id,
        meal_slot=meal_slot or "lunch",
        status="planned",
        recipe_id=recipe.get("recipe_id") or recipe.get("recipeId") or "",
        recipe_snapshot=recipe_snapshot,
        ingredients_used=requested,
        shopping_list=shopping_list,
        nutrition=_nutrition_from_recipe(recipe),
    )
    db.add(meal)
    await db.commit()
    await db.refresh(meal)
    await _persist_shopping_items(db, user_id, meal, shopping_list)
    return {
        "meal": _meal_dict(meal),
        "inventory_preview": {"deductions": deductions, "shopping_list": shopping_list},
        "shopping_list": shopping_list,
        "agent_events": _adopt_events(meal_slot or "lunch", deductions, shopping_list),
    }


async def ensure_shopping_list_table(db: AsyncSession) -> None:
    conn = await db.connection()
    await conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS shopping_list_items (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(32) NOT NULL,
            meal_id INT NULL,
            recipe_id VARCHAR(64) DEFAULT '',
            name VARCHAR(80) NOT NULL,
            amount INT NULL,
            unit VARCHAR(20) DEFAULT '',
            status VARCHAR(20) DEFAULT 'open',
            source VARCHAR(30) DEFAULT 'agent_adopt',
            meta JSON NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX ix_shopping_list_items_user_id (user_id),
            INDEX ix_shopping_list_items_meal_id (meal_id),
            INDEX ix_shopping_list_items_recipe_id (recipe_id),
            INDEX ix_shopping_list_items_name (name),
            INDEX ix_shopping_list_items_status (status)
        )
        """
    )


async def _persist_shopping_items(db: AsyncSession, user_id: str, meal: MealRecord, shopping_list: list[dict]) -> None:
    if not shopping_list:
        return
    await ensure_shopping_list_table(db)
    for item in shopping_list:
        name = _clean_name(item.get("name"))
        amount, unit = _parse_amount(item.get("amount") or item.get("display"))
        if item.get("unit"):
            unit = str(item.get("unit") or "").strip()
        if not name:
            continue
        db.add(ShoppingListItem(
            user_id=user_id,
            meal_id=meal.id,
            recipe_id=meal.recipe_id or "",
            name=name,
            amount=amount,
            unit=unit or "",
            status="open",
            source="agent_adopt",
            meta=item,
        ))
    await db.commit()


async def today_meals(db: AsyncSession, user_id: str) -> list[dict]:
    start = datetime.combine(date.today(), datetime.min.time())
    result = await db.execute(
        select(MealRecord)
        .where(MealRecord.user_id == user_id, MealRecord.created_at >= start)
        .order_by(MealRecord.created_at.desc())
    )
    return [_meal_dict(row) for row in result.scalars().all()]


async def today_shopping_list(db: AsyncSession, user_id: str) -> dict:
    await ensure_shopping_list_table(db)
    result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.user_id == user_id,
            ShoppingListItem.status == "open",
        ).order_by(ShoppingListItem.created_at.desc())
    )
    rows = result.scalars().all()
    if rows:
        merged: dict[tuple[str, str], dict] = {}
        for row in rows:
            key = (normalize_ingredient_name(row.name), row.unit or "")
            item = merged.setdefault(key, {
                "name": row.name,
                "amount": 0,
                "unit": row.unit or "",
                "display": "",
                "sources": [],
                "ids": [],
            })
            if row.amount is None:
                item["amount"] = None
            elif item["amount"] is not None:
                item["amount"] += int(row.amount or 0)
            item["ids"].append(row.id)
            item["sources"].append({"meal_id": row.meal_id, "recipe_id": row.recipe_id})
        items = []
        for item in merged.values():
            amount = item.get("amount")
            unit = item.get("unit") or ""
            item["display"] = f"{amount}{unit}" if amount is not None else ""
            items.append(item)
        return {"items": items, "count": len(items)}

    persisted_result = await db.execute(
        select(ShoppingListItem.id).where(ShoppingListItem.user_id == user_id).limit(1)
    )
    if persisted_result.scalar_one_or_none() is not None:
        return {"items": [], "count": 0}

    meals = await today_meals(db, user_id)
    merged: dict[tuple[str, str], dict] = {}
    for meal in meals:
        if meal.get("status") == "cancelled":
            continue
        for item in meal.get("shopping_list") or []:
            name = _clean_name(item.get("name"))
            amount, unit = _parse_amount(item.get("amount") or item.get("display"))
            if item.get("unit"):
                unit = str(item.get("unit") or "").strip()
            if not name:
                continue
            key = (normalize_ingredient_name(name), unit or "")
            current = merged.setdefault(key, {"name": name, "amount": 0, "unit": unit or "", "display": "", "sources": []})
            if amount is None:
                current["amount"] = None
            elif current["amount"] is not None:
                current["amount"] += amount
            current["sources"].append({"meal_id": meal.get("id"), "recipe_title": (meal.get("recipe") or {}).get("title", "")})
    items = []
    for item in merged.values():
        amount = item.get("amount")
        unit = item.get("unit") or ""
        item["display"] = f"{amount}{unit}" if amount is not None else ""
        items.append(item)
    return {"items": items, "count": len(items)}


def _shopping_item_dict(row: ShoppingListItem) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "amount": row.amount,
        "unit": row.unit or "",
        "display": f"{row.amount}{row.unit or ''}" if row.amount is not None else "",
        "status": row.status,
        "meal_id": row.meal_id,
        "recipe_id": row.recipe_id or "",
        "source": row.source or "",
        "meta": row.meta or {},
    }


async def update_shopping_item_status(
    db: AsyncSession,
    user_id: str,
    item_id: int,
    status: str,
) -> ShoppingListItem | None:
    await ensure_shopping_list_table(db)
    if status not in {"open", "purchased", "archived", "deleted"}:
        return None
    result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.id == item_id,
            ShoppingListItem.user_id == user_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None
    item.status = status
    await db.commit()
    await db.refresh(item)
    return item


async def archive_shopping_list(db: AsyncSession, user_id: str) -> dict:
    await ensure_shopping_list_table(db)
    result = await db.execute(
        select(ShoppingListItem).where(
            ShoppingListItem.user_id == user_id,
            ShoppingListItem.status == "open",
        )
    )
    rows = result.scalars().all()
    for row in rows:
        row.status = "archived"
    await db.commit()
    return {"archived_count": len(rows)}


async def complete_meal(db: AsyncSession, user_id: str, meal_id: int) -> MealRecord | None:
    result = await db.execute(select(MealRecord).where(MealRecord.id == meal_id, MealRecord.user_id == user_id))
    meal = result.scalar_one_or_none()
    if meal is None:
        return None
    if meal.status != "completed":
        meal.status = "completed"
        meal.completed_at = datetime.now()
        if not (meal.recipe_snapshot or {}).get("_agent_inventory_applied"):
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
