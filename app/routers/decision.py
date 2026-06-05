import json
from fastapi import APIRouter, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas import DecisionRequest, SuccessResponse, ErrorResponse
from app.models.recipe import Recipe
from app.services.decision import match_recipes
from app.services.nutrition import calc_gap
from app.core.database import get_db
from app.core import cache
from app.middleware.auth import get_optional_user
from app.services import user as user_svc

router = APIRouter()


@router.post("/v1/decision/meal-plan", tags=["Decision"])
async def generate_meal_plan(
    req: DecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict | None = Depends(get_optional_user),
):
    # 未登录时走缓存（无个性化差异）
    ings = sorted(req.ingredients)
    ck = cache.make_key("meal", json.dumps(ings), str(req.constraints))
    if not user:
        cached = await cache.get(ck)
        if cached:
            return SuccessResponse(data=cached)

    user_prefs = []
    goal = req.constraints.get("goal", "")
    if user:
        profile = await user_svc.get_profile(db, user["sub"])
        if profile:
            user_prefs = profile.get("preferences", [])
            goal = goal or profile.get("goal", "")

    recipes = await match_recipes(db, req.ingredients, req.constraints, user_prefs)
    ids = [r["recipe_id"] for r in recipes]
    gap = await calc_gap(db, ids, goal)
    result = {"recipes": recipes, "nutrition_gap": gap}

    if not user:
        await cache.set(ck, result)
    return SuccessResponse(data=result)
    # user_id 从 JWT 取，不从 body 取
    user_prefs = []
    goal = req.constraints.get("goal", "")
    if user:
        profile = await user_svc.get_profile(db, user["sub"])
        if profile:
            user_prefs = profile.get("preferences", [])
            goal = goal or profile.get("goal", "")

    recipes = await match_recipes(db, req.ingredients, req.constraints, user_prefs)
    ids = [r["recipe_id"] for r in recipes]
    gap = await calc_gap(db, ids, goal)

    return SuccessResponse(data={"recipes": recipes, "nutrition_gap": gap})


@router.get("/v1/recipes/{recipe_id}", tags=["Decision"])
async def get_recipe_detail(recipe_id: str = Path(...), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = r.scalar_one_or_none()
    if recipe is None:
        return ErrorResponse(error={"code": "NOT_FOUND", "message": "菜谱不存在"})
    return SuccessResponse(data={
        "recipe_id": recipe.id,
        "title": recipe.title,
        "steps": recipe.steps,
        "ingredients": recipe.ingredients,
        "calories": recipe.calories,
        "protein": recipe.protein,
        "cook_time": recipe.cook_time,
        "difficulty": recipe.difficulty,
    })
