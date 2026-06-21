from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import ErrorResponse, SuccessResponse
from app.services import favorites

router = APIRouter()


class FavoriteRequest(BaseModel):
    target_type: str
    target_id: str
    snapshot: dict = Field(default_factory=dict)


@router.get("/v1/favorites", tags=["Favorites"])
async def list_favorites(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data={"favorites": await favorites.list_favorites(db, user["sub"])})


@router.post("/v1/favorites", tags=["Favorites"])
async def add_favorite(req: FavoriteRequest, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        row = await favorites.add_favorite(db, user["sub"], req.target_type, req.target_id, req.snapshot)
    except ValueError as e:
        return ErrorResponse(error={"code": "INVALID_FAVORITE", "message": str(e)})
    return SuccessResponse(data={"favorite": favorites.favorite_dict(row)})


@router.delete("/v1/favorites", tags=["Favorites"])
async def delete_favorite(
    target_type: str = Query(...),
    target_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(data={"deleted": await favorites.delete_favorite(db, user["sub"], target_type, target_id)})


@router.get("/v1/favorites/status", tags=["Favorites"])
async def favorite_status(
    target_type: str = Query(...),
    target_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(data={"favorited": await favorites.favorite_status(db, user["sub"], target_type, target_id)})

