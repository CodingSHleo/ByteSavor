"""纠错日志服务：记录用户对识别/库存结果的修改，用于后续优化。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CorrectionLog


async def log_correction(
    db: AsyncSession,
    user_id: str,
    action: str,
    source: str = "sense",
    original_name: str = "",
    corrected_name: str = "",
    confidence: float = 0.0,
    meta: dict | None = None,
) -> CorrectionLog:
    record = CorrectionLog(
        user_id=user_id,
        source=source,
        action=action,
        original_name=original_name,
        corrected_name=corrected_name,
        confidence=int(confidence * 100),
        meta=meta or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_recent_corrections(
    db: AsyncSession,
    user_id: str,
    limit: int = 20,
) -> list[dict]:
    result = await db.execute(
        select(CorrectionLog)
        .where(CorrectionLog.user_id == user_id)
        .order_by(CorrectionLog.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [_row_to_dict(r) for r in rows]


async def get_recent_aliases(db: AsyncSession, user_id: str, limit: int = 30) -> list[dict]:
    """获取用户最近的改名纠错，返回别名映射列表。"""
    result = await db.execute(
        select(CorrectionLog)
        .where(CorrectionLog.user_id == user_id, CorrectionLog.action == "rename")
        .order_by(CorrectionLog.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    aliases = []
    for r in rows:
        if r.original_name and r.corrected_name:
            aliases.append({"from": r.original_name, "to": r.corrected_name})
    return aliases


def _row_to_dict(r: CorrectionLog) -> dict:
    return {
        "id": r.id,
        "source": r.source,
        "action": r.action,
        "original_name": r.original_name,
        "corrected_name": r.corrected_name,
        "confidence": r.confidence / 100 if r.confidence else 0,
        "meta": r.meta,
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }
