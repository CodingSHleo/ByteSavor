from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngredientInventory


def clean_name(name: str) -> str:
    return str(name or "").strip()


def _clean_unit(raw: str) -> str:
    """清理 unit 字段：去数字、去空格、统一小写。'100g' → 'g', '2 个' → '个'"""
    text = str(raw or "").strip()
    # 移除数字和空格
    text = re.sub(r"[\d\s]+", "", text)
    return text.lower()


def parse_amount(raw) -> tuple[int | None, str]:
    if raw is None:
        return None, ""
    if isinstance(raw, (int, float)):
        return int(raw), ""
    text = str(raw).strip()
    if not text:
        return None, ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z\u4e00-\u9fa5]*)", text)
    if not m:
        return None, text
    return int(float(m.group(1))), m.group(2) or ""


async def import_items(db: AsyncSession, user_id: str, items: list[dict], source: str = "manual") -> list[IngredientInventory]:
    saved = []
    for item in items:
        row = await upsert_item(db, user_id, item, source=source, commit=False)
        if row:
            saved.append(row)
    await db.commit()
    return saved


async def upsert_item(
    db: AsyncSession,
    user_id: str,
    item: dict,
    source: str = "manual",
    commit: bool = True,
) -> IngredientInventory | None:
    name = clean_name(item.get("name"))
    if not name:
        return None
    amount, unit = parse_amount(item.get("amount") or item.get("display") or item.get("weight_estimate"))
    if item.get("unit"):
        unit = _clean_unit(item.get("unit"))
    result = await db.execute(
        select(IngredientInventory).where(
            IngredientInventory.user_id == user_id,
            IngredientInventory.name == name,
            IngredientInventory.unit == (unit or ""),
        )
    )
    row = result.scalar_one_or_none()
    if row:
        if amount is not None:
            row.amount = int(row.amount or 0) + amount
        row.source = item.get("source") or source
        row.freshness = item.get("freshness") or row.freshness
        row.confidence = _confidence(item, row.confidence)
        row.meta = item
    else:
        row = IngredientInventory(
            user_id=user_id,
            name=name,
            amount=amount,
            unit=unit or "",
            source=item.get("source") or source,
            freshness=item.get("freshness") or "",
            confidence=_confidence(item, 0),
            meta=item,
        )
        db.add(row)
    if commit:
        await db.commit()
        await db.refresh(row)
    return row


async def add_item(db: AsyncSession, user_id: str, payload: dict) -> IngredientInventory:
    row = await upsert_item(db, user_id, payload, source=payload.get("source") or "manual", commit=True)
    if row is None:
        raise ValueError("食材名称不能为空")
    return row


async def update_item(db: AsyncSession, user_id: str, item_id: int, payload: dict) -> IngredientInventory | None:
    result = await db.execute(
        select(IngredientInventory).where(IngredientInventory.id == item_id, IngredientInventory.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    if "name" in payload and clean_name(payload.get("name")):
        row.name = clean_name(payload.get("name"))
    if "amount" in payload:
        amount, _unit = parse_amount(payload.get("amount"))
        row.amount = amount
    if "unit" in payload:
        row.unit = _clean_unit(payload.get("unit") or "")
    if "freshness" in payload:
        row.freshness = payload.get("freshness") or ""
    if "source" in payload:
        row.source = payload.get("source") or row.source
    meta = dict(row.meta or {})
    meta.update({k: v for k, v in payload.items() if v is not None})
    row.meta = meta
    await db.commit()
    await db.refresh(row)
    return row


async def delete_item(db: AsyncSession, user_id: str, item_id: int) -> bool:
    result = await db.execute(
        select(IngredientInventory).where(IngredientInventory.id == item_id, IngredientInventory.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def current_inventory(db: AsyncSession, user_id: str) -> list[dict]:
    result = await db.execute(
        select(IngredientInventory).where(IngredientInventory.user_id == user_id).order_by(IngredientInventory.updated_at.desc())
    )
    return [inventory_dict(row) for row in result.scalars().all()]


async def inventory_stats(db: AsyncSession, user_id: str) -> dict:
    items = await current_inventory(db, user_id)
    by_source: dict[str, int] = {}
    by_freshness: dict[str, int] = {}
    for item in items:
        by_source[item.get("source") or "unknown"] = by_source.get(item.get("source") or "unknown", 0) + 1
        by_freshness[item.get("freshness") or "unknown"] = by_freshness.get(item.get("freshness") or "unknown", 0) + 1
    return {
        "total_items": len(items),
        "total_amount_known": sum(1 for item in items if item.get("amount") is not None),
        "by_source": by_source,
        "by_freshness": by_freshness,
        "items": items,
    }


async def deduct_inventory(db: AsyncSession, user_id: str, used_items: list[dict]) -> None:
    for used in used_items:
        name = clean_name(used.get("name"))
        amount, unit = parse_amount(used.get("amount") or used.get("display"))
        if used.get("unit"):
            unit = _clean_unit(used.get("unit"))
        if not name or amount is None:
            continue
        result = await db.execute(
            select(IngredientInventory).where(
                IngredientInventory.user_id == user_id,
                IngredientInventory.name == name,
                IngredientInventory.unit == (unit or ""),
            )
        )
        row = result.scalar_one_or_none()
        if not row or row.amount is None:
            continue
        row.amount = max(0, int(row.amount or 0) - amount)


def inventory_dict(row: IngredientInventory) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "amount": row.amount,
        "unit": row.unit,
        "display": f"{row.amount} {row.unit}".strip() if row.amount is not None else "",
        "source": row.source,
        "freshness": row.freshness,
        "confidence": row.confidence,
        "meta": row.meta or {},
    }


def _confidence(item: dict, default: int) -> int:
    if not item.get("confidence"):
        return default
    try:
        value = float(item.get("confidence"))
        return int(value * 100) if value <= 1 else int(value)
    except Exception:
        return default

