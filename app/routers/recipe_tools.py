from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import SuccessResponse
from app.services import recipe_checker

router = APIRouter()


class RecipeCheckRequest(BaseModel):
    target_type: str = "system_recipe"
    target_id: str


@router.post("/v1/recipes/check", tags=["Decision"])
async def check_recipe(
    req: RecipeCheckRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(data=await recipe_checker.check_recipe(db, user["sub"], req.target_type, req.target_id))

