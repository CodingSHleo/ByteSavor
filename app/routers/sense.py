from fastapi import APIRouter
from app.schemas import SenseRequest, SuccessResponse, ErrorResponse
from app.services import vlm

router = APIRouter()

MOCK = {
    "ingredients": [
        {"name": "西兰花", "confidence": 0.98, "freshness": "high", "state": "新鲜"},
        {"name": "牛肉", "confidence": 0.95, "freshness": "normal", "state": "冷藏"},
    ],
    "portion_estimation": {"total_weight": 320},
}


@router.post("/v1/sense/analyze", tags=["Sense"])
async def analyze_ingredients(req: SenseRequest):
    if not req.image_url:
        return ErrorResponse(error={"code": "NO_IMAGE", "message": "缺少图片URL"})

    result = await vlm.analyze_food(req.image_url)
    if result is None or not result.get("ingredients"):
        result = MOCK

    return SuccessResponse(data=result)
