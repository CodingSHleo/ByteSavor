from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import ErrorResponse, SuccessResponse
from app.services import inventory

router = APIRouter()


class InventoryItemRequest(BaseModel):
    name: str = ""
    amount: int | float | str | None = None
    unit: str = ""
    source: str = "manual"
    freshness: str = ""
    confidence: int | float | None = None
    meta: dict = Field(default_factory=dict)


@router.post("/v1/inventory/items", tags=["Inventory"])
async def add_inventory_item(
    req: InventoryItemRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        row = await inventory.add_item(db, user["sub"], req.model_dump())
    except ValueError as e:
        return ErrorResponse(error={"code": "INVALID_INVENTORY_ITEM", "message": str(e)})
    return SuccessResponse(data={"item": inventory.inventory_dict(row)})


@router.put("/v1/inventory/items/{item_id}", tags=["Inventory"])
async def update_inventory_item(
    item_id: int,
    req: InventoryItemRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await inventory.update_item(db, user["sub"], item_id, req.model_dump(exclude_unset=True))
    if row is None:
        return ErrorResponse(error={"code": "INVENTORY_NOT_FOUND", "message": "食材不存在"})
    return SuccessResponse(data={"item": inventory.inventory_dict(row)})


@router.delete("/v1/inventory/items/{item_id}", tags=["Inventory"])
async def delete_inventory_item(
    item_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await inventory.delete_item(db, user["sub"], item_id)
    return SuccessResponse(data={"deleted": deleted})


@router.get("/v1/inventory/stats", tags=["Inventory"])
async def get_inventory_stats(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await inventory.inventory_stats(db, user["sub"]))

