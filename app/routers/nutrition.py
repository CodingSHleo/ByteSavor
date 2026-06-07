from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import SuccessResponse
from app.services.nutrition_analyzer import analyze_meal
from app.services import user as user_svc
from app.core.database import get_db
from app.middleware.auth import get_optional_user

router = APIRouter()


class MealRequest(BaseModel):
    image_url: str
    goal: str = "balanced"


@router.post("/v1/nutrition/analyze-meal", tags=["Nutrition"])
async def nutrition_analyze(req: MealRequest, db: AsyncSession = Depends(get_db), user: dict | None = Depends(get_optional_user)):
    goal = req.goal
    if user:
        profile = await user_svc.get_profile(db, user["sub"])
        if profile and profile.get("goal"):
            goal = profile["goal"]

    result = await analyze_meal(req.image_url, goal)
    return SuccessResponse(data=result)
