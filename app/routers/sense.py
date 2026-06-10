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
    # P0修复: 服务端图片大小校验，防DoS
    if len(req.image_url) > 8 * 1024 * 1024:  # 8MB上限
        return ErrorResponse(error={"code": "IMAGE_TOO_LARGE", "message": "图片过大，请压缩后重试"})

    result = await vlm.analyze_food(req.image_url)
    if result is None:
        logger.warning("vlm returned None; returning empty with hint")
        return SuccessResponse(data={
            "ingredients": [],
            "portion_estimation": {"total_weight": 0},
            "note": "图片上传成功，AI模型暂时繁忙，请重试或检查图片是否清晰"
        })

    return SuccessResponse(data=result)
