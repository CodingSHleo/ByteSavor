from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import ErrorResponse, SuccessResponse
from app.services import meal_memory

router = APIRouter()


class InventoryImportRequest(BaseModel):
    items: list[dict] = Field(default_factory=list)
    source: str = "manual"


class MealPlanRequest(BaseModel):
    meal_slot: str = "lunch"
    recipe: dict
    ingredients_used: list[dict] = Field(default_factory=list)
    shopping_list: list[dict] = Field(default_factory=list)


@router.post("/v1/inventory/import", tags=["Inventory"])
async def import_inventory(req: InventoryImportRequest, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await meal_memory.import_inventory(db, user["sub"], req.items, req.source)
    return SuccessResponse(data={"count": len(items)})


@router.get("/v1/inventory/current", tags=["Inventory"])
async def current_inventory(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data={"items": await meal_memory.current_inventory(db, user["sub"])})


@router.post("/v1/meals/plan", tags=["Meals"])
async def plan_meal(req: MealPlanRequest, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    meal = await meal_memory.plan_meal(db, user["sub"], req.meal_slot, req.recipe, req.ingredients_used, req.shopping_list)
    return SuccessResponse(data={"meal": meal_memory._meal_dict(meal)})


@router.get("/v1/meals/today", tags=["Meals"])
async def get_today_meals(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data={"meals": await meal_memory.today_meals(db, user["sub"])})


@router.post("/v1/meals/{meal_id}/complete", tags=["Meals"])
async def complete_meal(meal_id: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    meal = await meal_memory.complete_meal(db, user["sub"], meal_id)
    if meal is None:
        return ErrorResponse(error={"code": "MEAL_NOT_FOUND", "message": "用餐计划不存在"})
    return SuccessResponse(data={"meal": meal_memory._meal_dict(meal)})


@router.post("/v1/meals/{meal_id}/cancel", tags=["Meals"])
async def cancel_meal(meal_id: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    meal = await meal_memory.cancel_meal(db, user["sub"], meal_id)
    if meal is None:
        return ErrorResponse(error={"code": "MEAL_NOT_FOUND", "message": "用餐计划不存在"})
    return SuccessResponse(data={"meal": meal_memory._meal_dict(meal)})


@router.put("/v1/meals/{meal_id}/slot", tags=["Meals"])
async def change_meal_slot(meal_id: int, body: dict, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """切换用餐计划的 meal_slot（早餐→午餐等）。"""
    new_slot = body.get("meal_slot", "lunch")
    meal = await meal_memory.change_meal_slot(db, user["sub"], meal_id, new_slot)
    if meal is None:
        return ErrorResponse(error={"code": "MEAL_NOT_FOUND", "message": "用餐计划不存在"})
    return SuccessResponse(data={"meal": meal_memory._meal_dict(meal)})


@router.get("/v1/nutrition/summary", tags=["Nutrition"])
async def nutrition_summary(range: str = "day", user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await meal_memory.nutrition_summary(db, user["sub"], range))
