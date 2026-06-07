from fastapi import APIRouter
from app.schemas import SenseRequest, SuccessResponse, ErrorResponse
from app.services.quality import assess

router = APIRouter()


@router.post("/v1/quality/assess", tags=["Quality"])
async def assess_quality(req: SenseRequest):
    if not req.image_url:
        return ErrorResponse(error={"code": "NO_IMAGE", "message": "缺少图片URL"})
    result = await assess(req.image_url)
    return SuccessResponse(data=result)
