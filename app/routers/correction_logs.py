"""纠错日志接口：记录用户对识别/库存结果的修改操作。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import CorrectionLogRequest, SuccessResponse
from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.services import correction_logs as correction_svc

router = APIRouter()


@router.post("/v1/correction-logs", tags=["Correction"])
async def record_correction(
    body: CorrectionLogRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    record = await correction_svc.log_correction(
        db=db,
        user_id=user["sub"],
        action=body.action,
        source=body.source,
        original_name=body.original_name,
        corrected_name=body.corrected_name,
        confidence=body.confidence,
        meta=body.meta,
    )
    return SuccessResponse(data={"id": record.id, "acknowledged": True})


@router.get("/v1/correction-logs", tags=["Correction"])
async def list_corrections(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    limit: int = 20,
):
    records = await correction_svc.get_recent_corrections(db, user["sub"], limit=limit)
    return SuccessResponse(data={"corrections": records})
