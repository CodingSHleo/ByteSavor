import json
from fastapi import APIRouter, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas import DecisionRequest, SuccessResponse, ErrorResponse
from app.models.recipe import Recipe
from app.services.decision import match_recipes
from app.services.nutrition import calc_gap
from app.services.recipe_presenter import category, micro_highlights, micronutrients, recipe_brief
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


@router.get("/v1/recipes", tags=["Decision"])
async def list_recipes(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Recipe).order_by(Recipe.id))
    recipes = [recipe_brief(recipe) for recipe in r.scalars().all()]
    return SuccessResponse(data={"recipes": recipes, "total": len(recipes)})


@router.get("/v1/recipes/{recipe_id}", tags=["Decision"])
async def get_recipe_detail(recipe_id: str = Path(...), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = r.scalar_one_or_none()
    if recipe is None:
        return ErrorResponse(error={"code": "NOT_FOUND", "message": "菜谱不存在"})
    steps = recipe.steps
    if not steps or steps == [] or steps == ['详见原数据集']:
        names = [i['name'] for i in (recipe.ingredients or [])]
        steps = [f"准备食材：{'、'.join(names[:5])}"]
        if recipe.cook_time and recipe.cook_time > 20:
            steps.append(f"主料预处理（腌制/焯水/切配）")
        steps.append(f"热锅下油，依次下入主料翻炒/炖煮")
        if 'spicy' in (recipe.tags or []):
            steps.append("加入辣椒、花椒等调料调味")
        steps.append(f"总共烹饪约{recipe.cook_time or 30}分钟")
        steps.append("出锅装盘，趁热享用")

    return SuccessResponse(data={
        "recipe_id": recipe.id,
        "title": recipe.title,
        "steps": steps,
        "ingredients": recipe.ingredients,
        "calories": recipe.calories,
        "protein": recipe.protein,
        "cook_time": recipe.cook_time,
        "difficulty": recipe.difficulty,
        "category": category(recipe.tags),
        "tags": recipe.tags or [],
        "macros": {"protein": recipe.protein, "carbs": recipe.carbs, "fat": recipe.fat},
        "micronutrients": micronutrients(recipe),
        "micro_highlights": micro_highlights(micronutrients(recipe)),
        "story": getattr(recipe, 'story', '') or '',
        "culture_tags": getattr(recipe, 'culture_tags', []) or [],
    })
