import re
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe

_UNIT_NUMERIC = {"g", "ml", "kg", "l", "斤", "两", "个", "瓣", "根", "勺", "只", "条", "块", "把", "片"}


async def merge_shopping_list(db: AsyncSession, recipe_ids: list[str]) -> list[dict]:
    r = await db.execute(select(Recipe).where(Recipe.id.in_(recipe_ids)))
    recipes = r.scalars().all()

    merged: dict[str, list[dict]] = {}
    for rec in recipes:
        for ing in (rec.ingredients or []):
            name = ing.get("name", "")
            if not name:
                continue
            raw = ing.get("amount", "")
            q = _parse(raw)

            if name not in merged:
                merged[name] = [q]
                continue

            found = False
            for exist in merged[name]:
                if _can_merge(exist, q):
                    exist["value"] = (exist["value"] or 0) + (q["value"] or 0)
                    exist["display"] = _fmt_display(exist["value"], exist["unit"])
                    found = True
                    break
            if not found:
                merged[name].append(q)

    result = []
    for name, amounts in merged.items():
        if len(amounts) == 1:
            a = amounts[0]
            result.append({"name": name, "value": a["value"], "unit": a["unit"], "display": a["display"]})
        else:
            result.append({"name": name, "amounts": [
                {"value": a["value"], "unit": a["unit"], "display": a["display"]} for a in amounts
            ]})

    result.sort(key=lambda x: x["name"])
    return result


def _fmt_display(value, unit: str) -> str:
    if value is None:
        return unit
    if value == int(value):
        return f"{int(value)}{unit}"
    return f"{value}{unit}"


def _can_merge(a: dict, b: dict) -> bool:
    ua, ub = a.get("unit", ""), b.get("unit", "")
    if ua == ub and ua in _UNIT_NUMERIC:
        return True
    return False


def _parse(raw: str) -> dict:
    raw = str(raw).strip()
    if not raw:
        return {"value": None, "unit": "", "display": raw}
    m = re.match(r"([\d.]+)\s*([a-zA-Z]+|[一-鿿]+)", raw)
    if m:
        val = _clean_num(m.group(1))
        unit = m.group(2)
        return {"value": val, "unit": unit, "display": raw}
    return {"value": None, "unit": raw, "display": raw}


def _clean_num(s: str) -> float | None:
    try:
        v = float(s)
        return v if not math.isnan(v) else None
    except ValueError:
        return None
