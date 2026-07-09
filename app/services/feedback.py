from sqlalchemy.ext.asyncio import AsyncSession
import json

import httpx
from sqlalchemy import select
from app.core.config import settings
from app.models import Feedback, PreferenceMemory
from app.models.recipe import Recipe
from app.services.user import update_profile, get_profile

TAG_ALIASES = {
    "高蛋白": "high_protein",
    "蛋白": "high_protein",
    "增肌": "high_protein",
    "清淡": "light",
    "少油": "light",
    "低油": "light",
    "不油": "light",
    "香辣": "spicy",
    "麻辣": "spicy",
    "辣": "spicy",
    "低碳": "low_carb",
    "低碳水": "low_carb",
    "均衡": "balanced",
    "平衡": "balanced",
    "油腻": "oily",
    "太油": "oily",
}

METHOD_ALIASES = {
    "快炒": "stir_fry",
    "炒": "stir_fry",
    "小炒": "stir_fry",
    "蒸": "steam",
    "清蒸": "steam",
    "炖": "stew",
    "煮": "boil",
    "烤": "bake",
    "凉拌": "cold_mix",
}

CONSTRAINT_ALIASES = {
    "10分钟": "quick_meal",
    "15分钟": "quick_meal",
    "快手": "quick_meal",
    "很快": "quick_meal",
    "少油": "low_oil",
    "低油": "low_oil",
    "不油": "low_oil",
    "清淡": "light_taste",
}


async def ensure_preference_memory_table(db: AsyncSession) -> None:
    conn = await db.connection()
    await conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS preference_memories (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(32) NOT NULL,
            recipe_id VARCHAR(32) DEFAULT '',
            rating INT DEFAULT 0,
            comment VARCHAR(500) DEFAULT '',
            parsed JSON NULL,
            weight INT DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX ix_preference_memories_user_id (user_id),
            INDEX ix_preference_memories_recipe_id (recipe_id)
        )
        """
    )


def _extract_json(text: str) -> dict:
    content = (text or "").strip()
    if "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        if content.startswith("json"):
            content = content[4:].strip()
    if "{" in content and "}" in content:
        content = content[content.index("{"):content.rindex("}") + 1]
    return json.loads(content)


def _normalize_tag(raw: str) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    lower = text.lower()
    normalized = []
    for key, value in TAG_ALIASES.items():
        if key in text:
            normalized.append(value)
    for value in TAG_ALIASES.values():
        if value in lower:
            normalized.append(value)
    for part in lower.replace("，", "/").replace(",", "/").split("/"):
        part = part.strip()
        if part in set(TAG_ALIASES.values()):
            normalized.append(part)
    return list(dict.fromkeys(normalized or [lower]))


def _normalize_alias(raw: str, aliases: dict[str, str]) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    lower = text.lower()
    values = []
    for key, value in aliases.items():
        if key in text or value in lower:
            values.append(value)
    for part in lower.replace("，", "/").replace(",", "/").split("/"):
        part = part.strip()
        if part in set(aliases.values()):
            values.append(part)
    return list(dict.fromkeys(values or [lower]))


def _recipe_dict(recipe: Recipe | dict | None) -> dict:
    if not recipe:
        return {}
    if isinstance(recipe, dict):
        return recipe
    return {
        "title": recipe.title,
        "tags": recipe.tags or [],
        "ingredients": recipe.ingredients or [],
        "steps": recipe.steps or [],
    }


def _normalize_parsed_preference(parsed: dict) -> dict:
    parsed = parsed or {}
    out = {**parsed}
    for key in ("liked_tags", "avoid_tags"):
        values = []
        for item in parsed.get(key) or []:
            values.extend(_normalize_tag(item))
        out[key] = list(dict.fromkeys(values))[:12]
    for key in ("liked_ingredients", "liked_cuisines", "avoid_ingredients"):
        out[key] = [str(item).strip() for item in (parsed.get(key) or []) if str(item).strip()][:12]
    methods = []
    for item in parsed.get("liked_methods") or []:
        methods.extend(_normalize_alias(item, METHOD_ALIASES))
    out["liked_methods"] = list(dict.fromkeys(methods))[:12]
    constraints = []
    for item in parsed.get("constraints") or []:
        constraints.extend(_normalize_alias(item, CONSTRAINT_ALIASES))
    for source in [parsed.get("summary") or "", " ".join(parsed.get("liked_methods") or [])]:
        constraints.extend(_normalize_alias(source, CONSTRAINT_ALIASES))
    out["constraints"] = list(dict.fromkeys(constraints))[:12]
    out["evidence"] = [str(item).strip() for item in (parsed.get("evidence") or []) if str(item).strip()][:8]
    out["summary"] = str(parsed.get("summary") or "")[:160]
    return out


def _local_parse_preference(comment: str, recipe: Recipe | dict | None, rating: int) -> dict:
    text = comment or ""
    liked = rating >= 4
    disliked = rating <= 2
    recipe_data = _recipe_dict(recipe)
    tags = list(recipe_data.get("tags") or [])
    ingredients = [i.get("name") for i in (recipe_data.get("ingredients") or []) if isinstance(i, dict) and i.get("name")]
    steps_text = " ".join([str(step) for step in (recipe_data.get("steps") or [])])
    out = {
        "liked_tags": tags[:4] if liked else [],
        "liked_ingredients": ingredients[:4] if liked else [],
        "liked_cuisines": [],
        "liked_methods": [],
        "constraints": [],
        "avoid_tags": tags[:4] if disliked else [],
        "avoid_ingredients": ingredients[:4] if disliked else [],
        "evidence": [text[:80]] if text else [],
        "summary": text[:120],
    }
    if any(k in text for k in ("辣", "麻辣", "香辣")):
        (out["liked_tags"] if liked else out["avoid_tags"]).append("spicy")
    if any(k in text for k in ("清淡", "不油", "少油")):
        out["liked_tags"].append("light")
    if any(k in text for k in ("蛋白", "肉", "牛肉", "鸡胸")):
        out["liked_tags"].append("high_protein")
    if any(k in text for k in ("太油", "油腻")):
        out["avoid_tags"].append("oily")
    for source in (text, steps_text, recipe_data.get("title") or ""):
        out["liked_methods"].extend(_normalize_alias(source, METHOD_ALIASES))
        out["constraints"].extend(_normalize_alias(source, CONSTRAINT_ALIASES))
    return _normalize_parsed_preference(out)


async def _llm_parse_preference(comment: str, recipe: Recipe | dict | None, rating: int) -> dict:
    if not settings.llm_api_url or not comment:
        return {}
    recipe_info = _recipe_dict(recipe)
    prompt = f"""把用户对一道菜的反馈解析为偏好记忆。只返回JSON。
评分: {rating}/5
菜谱: {json.dumps(recipe_info, ensure_ascii=False)}
用户反馈: {comment}

格式:
{{
  "liked_tags": ["spicy/high_protein/light/low_carb/balanced等"],
  "liked_ingredients": ["食材"],
  "liked_cuisines": ["菜系"],
  "liked_methods": ["stir_fry/steam/stew/bake/cold_mix等"],
  "constraints": ["quick_meal/low_oil/light_taste等"],
  "avoid_tags": ["不喜欢的口味标签"],
  "avoid_ingredients": ["不喜欢的食材"],
  "evidence": ["触发该记忆的原句或菜谱特征"],
  "summary": "一句话总结"
}}"""
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_sec) as client:
            resp = await client.post(
                settings.llm_api_url,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400,
                    "temperature": 0,
                },
            )
            if resp.status_code != 200:
                return {}
            return _normalize_parsed_preference(_extract_json(resp.json()["choices"][0]["message"]["content"]))
    except Exception:
        return {}


async def get_preference_signals(db: AsyncSession, user_id: str) -> dict:
    await ensure_preference_memory_table(db)
    result = await db.execute(
        select(PreferenceMemory)
        .where(PreferenceMemory.user_id == user_id)
        .order_by(PreferenceMemory.created_at.desc())
        .limit(30)
    )
    memories = result.scalars().all()
    liked_tags, liked_ingredients, avoid_tags, avoid_ingredients = [], [], [], []
    liked_methods, constraints, evidence = [], [], []
    for memory in memories:
        parsed = memory.parsed or {}
        liked_tags.extend(parsed.get("liked_tags") or [])
        liked_ingredients.extend(parsed.get("liked_ingredients") or [])
        avoid_tags.extend(parsed.get("avoid_tags") or [])
        avoid_ingredients.extend(parsed.get("avoid_ingredients") or [])
        liked_methods.extend(parsed.get("liked_methods") or [])
        constraints.extend(parsed.get("constraints") or [])
        evidence.extend(parsed.get("evidence") or [])
    return {
        "liked_tags": list(dict.fromkeys(liked_tags))[:12],
        "liked_ingredients": list(dict.fromkeys(liked_ingredients))[:12],
        "avoid_tags": list(dict.fromkeys(avoid_tags))[:12],
        "avoid_ingredients": list(dict.fromkeys(avoid_ingredients))[:12],
        "liked_methods": list(dict.fromkeys(liked_methods))[:12],
        "constraints": list(dict.fromkeys(constraints))[:12],
        "evidence": list(dict.fromkeys(evidence))[:8],
    }


async def submit_feedback(db: AsyncSession, user_id: str, recipe_id: str, rating: int, comment: str = "", recipe_snapshot: dict | None = None) -> dict:
    fb = Feedback(user_id=user_id, recipe_id=recipe_id, rating=rating)
    db.add(fb)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    points = rating * 2

    # 偏好微调（非阻塞，失败不影响反馈写入）
    try:
        await ensure_preference_memory_table(db)
        r = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
        recipe = r.scalar_one_or_none() or (recipe_snapshot or None)
        parsed = await _llm_parse_preference(comment, recipe, rating)
        if not parsed:
            parsed = _local_parse_preference(comment, recipe, rating)
        else:
            fallback = _local_parse_preference(comment, recipe, rating)
            for key in ("liked_tags", "liked_ingredients", "liked_methods", "constraints", "avoid_tags", "avoid_ingredients", "evidence"):
                parsed[key] = list(dict.fromkeys((parsed.get(key) or []) + (fallback.get(key) or [])))[:12]
            parsed = _normalize_parsed_preference(parsed)
        db.add(PreferenceMemory(
            user_id=user_id,
            recipe_id=recipe_id,
            rating=rating,
            comment=comment or "",
            parsed=parsed,
            weight=max(1, rating),
        ))
        await db.commit()

        if isinstance(recipe, Recipe):
            profile = await get_profile(db, user_id)
            prefs = list(profile.get("preferences", []) if profile else [])
            tags = [t for t in recipe.tags if not t.startswith("quick")]
            tags = list(dict.fromkeys(tags + (parsed.get("liked_tags") or [])))

            if rating >= 4:
                added = [t for t in tags if t not in prefs]
                if added:
                    prefs.extend(added[:2])
            elif rating <= 2:
                prefs = [p for p in prefs if p not in tags]

            await update_profile(db, user_id, preferences=prefs[:8])
            # P1-5修复: 同步更新会话偏好(E→B回路)
            from app.services.session_prefs import add_session_prefs
            add_session_prefs(user_id, tags[:3])
    except Exception:
        pass

    return {"acknowledged": True, "reward_points": points}
