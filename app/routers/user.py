from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import SuccessResponse, ErrorResponse, ProfileUpdate
from app.services import user as user_svc
from app.core.database import get_db
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("/v1/user/profile", tags=["User"])
async def get_user_profile(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await user_svc.get_profile(db, user["sub"])
    if profile is None:
        return ErrorResponse(error={"code": "USER_NOT_FOUND", "message": "用户不存在"})
    return SuccessResponse(data=profile)


@router.put("/v1/user/profile", tags=["User"])
async def update_user_profile(
    req: ProfileUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await user_svc.update_profile(
        db,
        user["sub"],
        name=req.name,
        avatar_url=req.avatar_url,
        goal=req.goal,
        preferences=req.preferences,
        body_metrics=req.body_metrics,
        nutrition_targets=req.nutrition_targets,
    )
    profile = await user_svc.get_profile(db, user["sub"])
    return SuccessResponse(data=profile)


@router.get("/v1/nutrition/status", tags=["User"])
async def get_nutrition_status(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    status = await user_svc.get_nutrition_status(db, user["sub"])
    return SuccessResponse(data=status)
