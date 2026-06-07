from fastapi import APIRouter
from app.schemas import SenseRequest, SuccessResponse
from app.services.food_guide import guide

router = APIRouter()


@router.post("/v1/guide/explore", tags=["FoodGuide"])
async def explore_dish(req: SenseRequest):
    result = await guide(req.image_url)
    return SuccessResponse(data=result)
