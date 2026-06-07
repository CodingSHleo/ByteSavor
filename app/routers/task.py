from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import MergeRequest, SuccessResponse, ErrorResponse
from app.services.shopping import merge_shopping_list as do_merge
from app.services.ingredient_tips import enrich_shopping_list
from app.core.database import get_db

router = APIRouter()


@router.post("/v1/task/merge-list", tags=["Task"])
async def merge_list(req: MergeRequest, db: AsyncSession = Depends(get_db)):
    if not req.recipes:
        return ErrorResponse(error={"code": "NO_RECIPES", "message": "未选择菜谱"})
    items = await do_merge(db, req.recipes)
    items = enrich_shopping_list(items)
    return SuccessResponse(data={"shopping_list": items})
