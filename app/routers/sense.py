import logging

from fastapi import APIRouter
from app.schemas import SenseRequest, SuccessResponse, ErrorResponse
from app.services import vlm
from app.services.vlm.openai import VLMProviderError

router = APIRouter()
logger = logging.getLogger("sense")


@router.post("/v1/sense/analyze", tags=["Sense"])
async def analyze_ingredients(req: SenseRequest):
    if not req.image_url:
        return ErrorResponse(error={"code": "NO_IMAGE", "message": "缺少图片URL"})
    # P0修复: 服务端图片大小校验，防DoS
    if len(req.image_url) > 8 * 1024 * 1024:  # 8MB上限
        return ErrorResponse(error={"code": "IMAGE_TOO_LARGE", "message": "图片过大，请压缩后重试"})

    try:
        result = await vlm.analyze_food(req.image_url)
    except VLMProviderError as exc:
        logger.warning("vlm provider error code=%s message=%s", exc.code, exc.message)
        return ErrorResponse(error={
            "code": exc.code,
            "message": exc.message,
        })
    if result is None:
        logger.warning("vlm returned None; returning explicit unavailable error")
        return ErrorResponse(error={
            "code": "VLM_UNAVAILABLE",
            "message": "AI视觉模型暂时不可用，请稍后重试",
        })

    return SuccessResponse(data=result)
