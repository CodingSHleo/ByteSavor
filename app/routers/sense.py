import logging

from fastapi import APIRouter
from app.schemas import SenseRequest, SuccessResponse, ErrorResponse
from app.services import vlm

router = APIRouter()
logger = logging.getLogger("sense")


@router.post("/v1/sense/analyze", tags=["Sense"])
async def analyze_ingredients(req: SenseRequest):
    if not req.image_url:
        return ErrorResponse(error={"code": "NO_IMAGE", "message": "缺少图片URL"})

    result = await vlm.analyze_food(req.image_url)
    if result is None:
        logger.warning("vlm returned None; returning explicit unavailable error")
        return ErrorResponse(error={
            "code": "VLM_UNAVAILABLE",
            "message": "视觉模型暂不可用，未使用本地模拟识别结果",
        })
    elif not result.get("ingredients"):
        return SuccessResponse(data={
            "ingredients": [],
            "portion_estimation": {"total_weight": 0},
            "note": "VLM未检测到食材"
        })

    return SuccessResponse(data=result)
