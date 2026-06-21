from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RecipeFavorite

VALID_TARGET_TYPES = {"system_recipe", "community_post"}


async def add_favorite(db: AsyncSession, user_id: str, target_type: str, target_id: str, snapshot: dict | None = None) -> RecipeFavorite:
    _validate(target_type, target_id)
    result = await db.execute(
        select(RecipeFavorite).where(
            RecipeFavorite.user_id == user_id,
            RecipeFavorite.target_type == target_type,
            RecipeFavorite.target_id == str(target_id),
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.snapshot = snapshot or row.snapshot or {}
    else:
        row = RecipeFavorite(user_id=user_id, target_type=target_type, target_id=str(target_id), snapshot=snapshot or {})
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_favorites(db: AsyncSession, user_id: str) -> list[dict]:
    result = await db.execute(
        select(RecipeFavorite)
        .where(RecipeFavorite.user_id == user_id)
        .order_by(RecipeFavorite.created_at.desc(), RecipeFavorite.id.desc())
    )
    return [favorite_dict(row) for row in result.scalars().all()]


async def delete_favorite(db: AsyncSession, user_id: str, target_type: str, target_id: str) -> bool:
    result = await db.execute(
        select(RecipeFavorite).where(
            RecipeFavorite.user_id == user_id,
            RecipeFavorite.target_type == target_type,
            RecipeFavorite.target_id == str(target_id),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def favorite_status(db: AsyncSession, user_id: str, target_type: str, target_id: str) -> bool:
    result = await db.execute(
        select(RecipeFavorite.id).where(
            RecipeFavorite.user_id == user_id,
            RecipeFavorite.target_type == target_type,
            RecipeFavorite.target_id == str(target_id),
        )
    )
    return result.scalar_one_or_none() is not None


async def favorite_status_map(db: AsyncSession, user_id: str, target_type: str, target_ids: list[str]) -> dict[str, bool]:
    ids = [str(target_id) for target_id in target_ids if str(target_id or "").strip()]
    if not ids:
        return {}
    result = await db.execute(
        select(RecipeFavorite.target_id).where(
            RecipeFavorite.user_id == user_id,
            RecipeFavorite.target_type == target_type,
            RecipeFavorite.target_id.in_(ids),
        )
    )
    favorited = {str(row[0]) for row in result.all()}
    return {target_id: target_id in favorited for target_id in ids}


def favorite_dict(row: RecipeFavorite) -> dict:
    return {
        "id": row.id,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "snapshot": row.snapshot or {},
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def _validate(target_type: str, target_id: str) -> None:
    if target_type not in VALID_TARGET_TYPES:
        raise ValueError("不支持的收藏类型")
    if not str(target_id or "").strip():
        raise ValueError("收藏目标不能为空")
