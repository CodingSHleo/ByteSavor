from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CommunityPost
from app.models.recipe import Recipe
from app.services import inventory as inventory_svc


async def check_recipe(db: AsyncSession, user_id: str, target_type: str, target_id: str) -> dict:
    recipe = await _load_recipe(db, target_type, target_id)
    if recipe is None:
        return {
            "target": {"target_type": target_type, "target_id": target_id, "title": ""},
            "owned": [],
            "missing": [],
            "shopping_list": [],
            "fit_ratio": 0,
            "can_cook": False,
            "error": "RECIPE_NOT_FOUND",
        }
    inventory = await inventory_svc.current_inventory(db, user_id)
    owned, missing = _compare(recipe.get("ingredients") or [], inventory)
    total = len(owned) + len(missing)
    fit_ratio = round(len(owned) / total, 2) if total else 0
    return {
        "target": {
            "target_type": target_type,
            "target_id": target_id,
            "title": recipe.get("title") or "",
            "recipe": recipe,
        },
        "owned": owned,
        "missing": missing,
        "shopping_list": [{"name": item["name"], "amount": item["shortage"] or item["required"]} for item in missing],
        "fit_ratio": fit_ratio,
        "can_cook": bool(total and not missing),
    }


async def _load_recipe(db: AsyncSession, target_type: str, target_id: str) -> dict | None:
    if target_type == "system_recipe":
        result = await db.execute(select(Recipe).where(Recipe.id == target_id))
        recipe = result.scalar_one_or_none()
        if recipe is None:
            return None
        return {
            "recipe_id": recipe.id,
            "title": recipe.title,
            "ingredients": recipe.ingredients or [],
            "steps": recipe.steps or [],
            "calories": recipe.calories,
            "macros": {"protein": recipe.protein, "carbs": recipe.carbs, "fat": recipe.fat},
            "cook_time": recipe.cook_time,
            "tags": recipe.tags or [],
            "source": "system",
        }
    if target_type == "community_post":
        result = await db.execute(select(CommunityPost).where(CommunityPost.id == int(target_id)))
        post = result.scalar_one_or_none()
        if post is None or post.category != "recipe":
            return None
        payload = post.recipe_payload or {}
        return {
            "recipe_id": f"community_{post.id}",
            "title": payload.get("title") or post.title,
            "ingredients": payload.get("ingredients") or [],
            "steps": payload.get("steps") or [],
            "calories": payload.get("calories") or 0,
            "macros": payload.get("macros") or {},
            "source": "community",
            "post_id": post.id,
        }
    return None


def _compare(required: list, current: list[dict]) -> tuple[list[dict], list[dict]]:
    inventory_by_name = {inventory_svc.clean_name(item.get("name")): item for item in current}
    owned = []
    missing = []
    for raw in required:
        item = raw if isinstance(raw, dict) else {"name": str(raw), "amount": ""}
        name = inventory_svc.clean_name(item.get("name"))
        if not name:
            continue
        required_amount, required_unit = inventory_svc.parse_amount(item.get("amount") or item.get("display"))
        available = inventory_by_name.get(name)
        if not available:
            missing.append(_missing_item(name, item, None, required_amount, required_unit))
            continue
        available_amount = available.get("amount")
        available_unit = available.get("unit") or ""
        if required_amount is None or not required_unit:
            owned.append(_owned_item(name, item, available, "needs_review"))
        elif available_unit == required_unit and available_amount is not None and int(available_amount) >= required_amount:
            owned.append(_owned_item(name, item, available, "enough"))
        elif available_unit == required_unit:
            missing.append(_missing_item(name, item, available, required_amount - int(available_amount or 0), required_unit))
        else:
            missing.append(_missing_item(name, item, available, required_amount, required_unit, needs_review=True))
    return owned, missing


def _owned_item(name: str, required: dict, available: dict, status: str) -> dict:
    return {
        "name": name,
        "required": required.get("amount") or required.get("display") or "",
        "available": available.get("display") or "",
        "status": status,
    }


def _missing_item(
    name: str,
    required: dict,
    available: dict | None,
    shortage_amount: int | None,
    shortage_unit: str,
    needs_review: bool = False,
) -> dict:
    shortage = f"{shortage_amount}{shortage_unit}" if shortage_amount is not None else (required.get("amount") or "")
    return {
        "name": name,
        "required": required.get("amount") or required.get("display") or "",
        "available": (available or {}).get("display") or "",
        "shortage": shortage,
        "status": "needs_review" if needs_review else "missing",
    }

