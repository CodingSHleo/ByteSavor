import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe
from app.services.food_synonyms import normalize_ingredient_name as normalize_synonym
from app.services.llm_rerank import rerank_recipe_candidates
from app.services.recipe_presenter import recipe_brief

logger = logging.getLogger("decision")

PREFERENCE_ALIASES = {
    "清淡": "light",
    "少油": "light",
    "低油": "light",
    "不油": "light",
    "香辣": "spicy",
    "麻辣": "spicy",
    "辣": "spicy",
    "高蛋白": "high_protein",
    "蛋白": "high_protein",
    "低碳": "low_carb",
    "低碳水": "low_carb",
    "素食": "vegetarian",
    "蔬菜": "vegetarian",
    "海鲜": "seafood",
    "鱼": "seafood",
    "虾": "seafood",
}


async def recommend(db: AsyncSession, ingredients: list[str], constraints: dict, user_prefs: list[str]) -> list[dict]:
    """推荐 pipeline：检索 → 硬过滤 → 软排序 → 解释生成 → fallback"""
    t0 = time.time()
    taste = constraints.get("taste", "")
    goal = constraints.get("goal", "")
    time_limit = constraints.get("time_limit", 999)
    avoid_tags = constraints.get("avoid_tags", []) or []
    avoid_ingredients = constraints.get("avoid_ingredients", []) or []
    exclude_recipe_ids = {str(x) for x in constraints.get("exclude_recipe_ids", []) or []}
    is_explore = len(ingredients) == 0

    # ---- 1. 候选检索 + SQL层硬过滤 ----
    recipes = await _retrieve(db, time_limit)

    # ---- 2. 硬过滤（已在SQL完成，保留Python层做兜底） ----
    candidates = _hard_filter(recipes, time_limit)

    # ---- 3. 排序 ----
    if is_explore:
        scored = _explore_rank(candidates, taste, goal, user_prefs, avoid_tags, avoid_ingredients)
    else:
        scored = _rank(candidates, ingredients, taste, goal, user_prefs, avoid_tags, avoid_ingredients)
    if exclude_recipe_ids:
        filtered_scored = [r for r in scored if str(r.get("recipe_id")) not in exclude_recipe_ids]
        if filtered_scored:
            scored = filtered_scored
    scored = await _maybe_llm_rerank(scored, ingredients, constraints)
    scored.sort(key=lambda x: (x.get("_group_priority", 9), -x["match_score"]))

    is_fallback = False
    # ---- 4. Fallback：无结果时放宽条件（在解释生成前） ----
    if not scored:
        if not candidates:
            candidates = recipes
        scored = _fallback(candidates, taste, goal)
        is_fallback = True

    # ---- 5. 解释生成 ----
    for s in scored:
        s["reasons"] = _build_reasons(s.pop("_codes", []))

    elapsed = round((time.time() - t0) * 1000)
    logger.info("decision_result", extra={
        "ingredients": ingredients, "time_limit": time_limit, "taste": taste, "goal": goal,
        "is_explore": is_explore, "results": len(scored), "latency_ms": elapsed,
        "top": scored[0]["title"] if scored else "none",
    })

    result = scored[:8]
    for r in result:
        r.pop("_group_priority", None)
        r["fallback"] = is_fallback
        result_meta = _recipe_match_meta(r, ingredients)
        if result_meta:
            r["_meta"] = result_meta
    return result


async def _maybe_llm_rerank(scored: list[dict], ingredients: list[str], constraints: dict) -> list[dict]:
    ranked_ids = await rerank_recipe_candidates(
        user_ingredients=ingredients,
        constraints=constraints,
        candidates=scored,
    )
    if not ranked_ids:
        return scored
    by_id = {str(item.get("recipe_id")): item for item in scored}
    seen = set()
    reranked = []
    for recipe_id in ranked_ids:
        item = by_id.get(recipe_id)
        if item is not None and recipe_id not in seen:
            item["llm_reranked"] = True
            reranked.append(item)
            seen.add(recipe_id)
    reranked.extend(item for item in scored if str(item.get("recipe_id")) not in seen)
    return reranked


def _recommend_meta(scored: list[dict], user_ings: list[str]) -> dict:
    """生成推荐解释元数据：完全匹配食材、缺失食材。"""
    if not user_ings or not scored:
        return {}
    norm_user = {_normalize_ingredient_name(u) for u in user_ings if str(u).strip()}
    all_recipe_names = set()
    for r in scored:
        ri = [i.get("name", "") for i in (r.get("ingredients", []) or [])]
        for name in ri:
            all_recipe_names.add(_normalize_ingredient_name(name))
    exact = {u for u in norm_user if any(_ingredient_matches(rn, u) for rn in all_recipe_names)}
    missing = sorted(norm_user - exact)
    return {
        "matched_ingredients": sorted(exact),
        "missing_ingredients": missing,
        "total_results": len(scored),
    }


def _recipe_match_meta(recipe: dict, user_ings: list[str]) -> dict:
    if not user_ings:
        return {}
    norm_user = [_normalize_ingredient_name(u) for u in user_ings if str(u).strip()]
    recipe_ingredients = [i for i in (recipe.get("ingredients", []) or []) if isinstance(i, dict)]
    recipe_names = [_normalize_ingredient_name(i.get("name", "")) for i in recipe_ingredients]
    matched = []
    missing = []
    for user_ing in norm_user:
        if any(_ingredient_matches(recipe_name, user_ing) for recipe_name in recipe_names):
            matched.append(user_ing)
        else:
            missing.append(user_ing)
    purchase_suggestions = []
    for ingredient in recipe_ingredients:
        recipe_name = _normalize_ingredient_name(ingredient.get("name", ""))
        if not recipe_name:
            continue
        if any(_ingredient_matches(recipe_name, user_ing) for user_ing in norm_user):
            continue
        purchase_suggestions.append({
            "name": ingredient.get("name", ""),
            "amount": ingredient.get("amount", ""),
        })
    return {
        "matched_ingredients": sorted(set(matched)),
        "missing_ingredients": sorted(set(missing)),
        "purchase_suggestions": purchase_suggestions[:5],
        "preference_matches": recipe.get("_preference_matches", []),
    }


# ---------- 1. 候选检索 ----------
async def _retrieve(db: AsyncSession, time_limit: int = 999) -> list[Recipe]:
    q = select(Recipe)
    if time_limit < 999:
        q = q.where(Recipe.cook_time <= time_limit)
    r = await db.execute(q)
    return list(r.scalars().all())


# ---------- 2. 硬过滤 ----------
def _hard_filter(recipes: list[Recipe], time_limit: int) -> list[Recipe]:
    return [r for r in recipes if r.cook_time <= time_limit]


# ---------- 3a. 普通排序 ----------
def _rank(recipes: list[Recipe], ingredients: list[str], taste: str, goal: str, prefs: list[str], avoid_tags: list[str] | None = None, avoid_ingredients: list[str] | None = None) -> list[dict]:
    # ── 批次A: 核心食材硬约束 ──
    user_ings = [_normalize_ingredient_name(u) for u in (ingredients or []) if str(u).strip()]
    full_match = []
    specific_match = []
    partial_match = []
    unmatched = []
    for r in recipes:
        if user_ings:
            coverage = _get_user_ingredient_coverage(r, user_ings)
            r._user_coverage = coverage
            if coverage == 0:
                unmatched.append(r)  # 完全不匹配用户食材 → 排除
            elif coverage >= 1.0:
                r._user_match_group = 0
                full_match.append(r)
            elif _matches_specific_requested_ingredient(r, user_ings):
                r._user_match_group = 1
                specific_match.append(r)
            else:
                r._user_match_group = 2
                partial_match.append(r)
        else:
            r._user_coverage = 1.0
            r._user_match_group = 0
            full_match.append(r)

    # 用户给出食材时，推荐必须围绕现有食材展开：
    # 1. 全部覆盖；2. 覆盖更具体/稀缺食材；3. 仅部分覆盖；4. 无匹配仅作 fallback。
    candidates = full_match + specific_match + partial_match
    if not candidates:
        candidates = unmatched
        for r in candidates:
            r._user_match_group = 3

    scored = []
    for r in candidates:
        s_ing, codes_ing = _calc_ingredient_fixed(r, user_ings)
        s_tag, codes_tag = _calc_tag(r, taste, goal)
        s_pref, codes_pref = _calc_pref(r, prefs)
        penalty, codes_penalty = _calc_avoid(r, avoid_tags or [], avoid_ingredients or [])
        # 用户食材覆盖率权重提升：完全命中 → 高权重；部分命中 → 降权
        ing_weight = 0.55
        s = s_ing * ing_weight + s_tag * 0.25 + s_pref * 0.2
        s = max(0, s - penalty)
        # 完全命中用户食材 → 额外加分
        if user_ings and hasattr(r, '_user_coverage') and r._user_coverage >= 1.0:
            s += 0.1
        elif user_ings and _matches_specific_requested_ingredient(r, user_ings):
            s += 0.08
        if s > 0.2:
            item = {
                **recipe_brief(r),
                "match_score": round(min(s, 1.0), 2),
                "_codes": codes_ing + codes_tag + codes_pref + codes_penalty,
                "_group_priority": getattr(r, "_user_match_group", 9),
            }
            item["_preference_matches"] = [meta.get("pref") for code, meta in codes_pref if code == "PREF_MATCH" and meta.get("pref")]
            item["_meta"] = _recipe_match_meta(item, ingredients)
            scored.append(item)
    scored.sort(key=lambda x: (x.get("_group_priority", 9), -x["match_score"]))
    return scored


def _get_user_ingredient_coverage(r: Recipe, user_ings: list[str]) -> float:
    """返回用户食材被菜谱覆盖的比例。"""
    if not r.ingredients or not user_ings:
        return 0.0
    recipe_names = {_normalize_ingredient_name(i.get("name", "")) for i in r.ingredients if isinstance(i, dict)}
    recipe_names = {n for n in recipe_names if n}
    if not recipe_names:
        return 0.0
    matched = 0
    for ui in user_ings:
        for rn in recipe_names:
            if _ingredient_matches(rn, ui):
                matched += 1
                break
    return matched / len(user_ings)


def _matches_specific_requested_ingredient(r: Recipe, user_ings: list[str]) -> bool:
    """优先使用更具体的用户食材，避免泛化主料压过韭黄/南瓜等关键搭配。"""
    if not r.ingredients or not user_ings:
        return False
    recipe_names = {
        _normalize_ingredient_name(i.get("name", ""))
        for i in r.ingredients
        if isinstance(i, dict)
    }
    for user_ing in sorted(set(user_ings), key=len, reverse=True):
        if len(user_ing) < 2:
            continue
        if user_ing in {"牛肉", "猪肉", "鸡肉", "羊肉", "鱼", "虾", "蛋", "鸡蛋"}:
            continue
        if any(_ingredient_matches(recipe_name, user_ing) for recipe_name in recipe_names):
            return True
    return False


def _calc_ingredient_fixed(r: Recipe, user_ings: list[str]) -> tuple[float, list]:
    """食材匹配打分（批次A修正版）：用户覆盖率权重提升，完全命中加分。"""
    if not r.ingredients or not user_ings:
        return 0.3, []
    recipe_names = {_normalize_ingredient_name(i.get("name", "")) for i in r.ingredients if isinstance(i, dict)}
    recipe_names = {name for name in recipe_names if name}
    user_set = {u for u in user_ings if str(u).strip()}
    exact = {u for u in user_set if any(_ingredient_matches(recipe_name, u) for recipe_name in recipe_names)}
    recipe_hit_count = sum(1 for recipe_name in recipe_names if any(_ingredient_matches(recipe_name, u) for u in user_set))
    recipe_coverage = recipe_hit_count / len(recipe_names) if recipe_names else 0
    user_coverage = len(exact) / len(user_set) if user_set else 0
    # 用户食材覆盖率主导
    score = recipe_coverage * 0.2 + user_coverage * 0.8
    if user_set and exact == user_set:
        score += 0.15
    score = min(score, 1.0)
    codes = [("ING_MATCH", {"ingredient": e}) for e in sorted(exact)]
    # 缺失食材
    missing = sorted(user_set - exact)
    if missing:
        codes.append(("ING_MISSING", {"ingredient": ", ".join(missing[:3])}))
    return score, codes


# ---------- 3b. 探索排序 ----------
def _explore_rank(recipes: list[Recipe], taste: str, goal: str, prefs: list[str], avoid_tags: list[str] | None = None, avoid_ingredients: list[str] | None = None) -> list[dict]:
    scored = []
    for r in recipes:
        s_tag, codes_tag = _calc_tag(r, taste, goal)
        s_pref, codes_pref = _calc_pref(r, prefs)
        penalty, codes_penalty = _calc_avoid(r, avoid_tags or [], avoid_ingredients or [])
        s = s_tag * 0.6 + s_pref * 0.4
        s = max(0, s - penalty)
        codes = codes_tag + codes_pref + codes_penalty
        if "quick" in [t.lower() for t in r.tags]:
            codes.append(("QUICK", {"time": r.cook_time}))
            s += 0.05
        if s > 0.3:
            scored.append({**recipe_brief(r), "match_score": round(min(s, 1.0), 2), "_codes": codes})
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


# ---------- 4. 解释生成 ----------
REASON_TEMPLATES = {
    "ING_MATCH": "已有食材: {ingredient}",
    "ING_MISSING": "缺少: {ingredient}",
    "TASTE_MATCH": "口味匹配: {taste}",
    "LOW_CARB": "低碳水",
    "HIGH_PROTEIN_GOAL": "高蛋白适合{goal}",
    "BALANCED": "营养均衡",
    "PREF_MATCH": "符合偏好: {pref}",
    "MEMORY_MATCH": "基于历史偏好推荐",
    "INVENTORY_MATCH": "库存可做: {item}",
    "QUICK": "{time}分钟快速完成",
    "NEAR_FIT": "接近匹配: {title}",
    "AVOID_DOWNRANK": "已降低不喜欢项: {item}",
}

def _build_reasons(codes: list[tuple]) -> list[dict]:
    reasons = []
    for code, meta in codes:
        tmpl = REASON_TEMPLATES.get(code, code)
        try:
            text = tmpl.format(**meta)
        except KeyError:
            text = tmpl
        reasons.append({"code": code, "text": text, "meta": meta})
    return reasons


# ---------- 5. Fallback ----------
def _fallback(recipes: list[Recipe], taste: str, goal: str) -> list[dict]:
    """无结果时放宽所有条件，返回最接近的推荐"""
    scored = _explore_rank(recipes, taste, goal, [])
    all_ids = {s["recipe_id"] for s in scored}
    for r in recipes:
        if r.id not in all_ids:
            scored.append({**recipe_brief(r), "match_score": 0.15, "_codes": [("NEAR_FIT", {"title": r.title})]})
    for s in scored:
        s["_codes"].append(("NEAR_FIT", {"title": s["title"]}))
        s["match_score"] = round(s["match_score"] * 0.5, 2)
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


# ---------- 子打分函数 ----------
def _calc_ingredient(r: Recipe, user_ings: list[str]) -> tuple[float, list]:
    if not r.ingredients or not user_ings:
        return 0.3, []  # 无食材时给基准分
    recipe_names = {_normalize_ingredient_name(i.get("name", "")) for i in r.ingredients if isinstance(i, dict)}
    recipe_names = {name for name in recipe_names if name}
    user_set = {_normalize_ingredient_name(u) for u in user_ings if str(u).strip()}
    exact = {u for u in user_set if any(_ingredient_matches(recipe_name, u) for recipe_name in recipe_names)}
    recipe_hit_count = sum(1 for recipe_name in recipe_names if any(_ingredient_matches(recipe_name, u) for u in user_set))
    # 用户明确说出的食材是强约束，优先保证覆盖用户侧，再兼顾菜谱侧覆盖。
    recipe_coverage = recipe_hit_count / len(recipe_names) if recipe_names else 0
    user_coverage = len(exact) / len(user_set) if user_set else 0
    score = recipe_coverage * 0.35 + user_coverage * 0.65
    if user_set and exact == user_set:
        score += 0.12
    score = min(score, 1.0)
    codes = [("ING_MATCH", {"ingredient": e}) for e in sorted(exact)]
    return score, codes


def _normalize_ingredient_name(value: str) -> str:
    text = str(value or "").lower().strip()
    for token in ("适量", "少许", "去皮", "切片", "切块", "切丝", "新鲜", "嫩", "老", "泥", "末", "丝", "片", "块"):
        text = text.replace(token, "")
    # P1-8: 复用同义词标准化
    return normalize_synonym(text).lower().strip()


def _ingredient_matches(recipe_name: str, user_name: str) -> bool:
    if not recipe_name or not user_name:
        return False
    return recipe_name == user_name or recipe_name in user_name or user_name in recipe_name


def _calc_tag(r: Recipe, taste: str, goal: str) -> tuple[float, list]:
    score = 0.2  # 基准
    codes = []
    tags = [t.lower() for t in r.tags]
    if taste and taste.lower() in tags:
        score += 0.3
        codes.append(("TASTE_MATCH", {"taste": taste}))
    if goal == "fat_loss":
        if "low_carb" in tags:
            score += 0.25
            codes.append(("LOW_CARB", {}))
        if "high_protein" in tags:
            score += 0.25
            codes.append(("HIGH_PROTEIN_GOAL", {"goal": "减脂"}))
    elif goal == "muscle_gain" and "high_protein" in tags:
        score += 0.4
        codes.append(("HIGH_PROTEIN_GOAL", {"goal": "增肌"}))
    elif goal == "balanced" and "balanced" in tags:
        score += 0.3
        codes.append(("BALANCED", {}))
    return min(score, 1.0), codes


def _calc_pref(r: Recipe, prefs: list[str]) -> tuple[float, list]:
    if not prefs:
        return 0.5, []
    tags = {str(t).lower() for t in (r.tags or [])}
    title = str(getattr(r, "title", "") or "").lower()
    ingredient_text = " ".join(str(i.get("name", "")) for i in (r.ingredients or []) if isinstance(i, dict)).lower()
    normalized_prefs = _normalize_preferences(prefs)
    hits = []
    for pref in normalized_prefs:
        if pref in tags or pref in title or pref in ingredient_text:
            hits.append(pref)
    score = min(0.5 + len(hits) * 0.2, 1.0)
    codes = [("PREF_MATCH", {"pref": h}) for h in hits[:3]]
    return score, codes


def _normalize_preferences(prefs: list[str]) -> list[str]:
    normalized = []
    for pref in prefs or []:
        raw = str(pref or "").strip()
        if not raw:
            continue
        lower = raw.lower()
        matched = False
        for key, value in PREFERENCE_ALIASES.items():
            if key in raw or value in lower:
                normalized.append(value)
                matched = True
        if not matched:
            normalized.append(lower)
    return list(dict.fromkeys(normalized))


def _calc_avoid(r: Recipe, avoid_tags: list[str], avoid_ingredients: list[str]) -> tuple[float, list]:
    tags = {str(t).lower() for t in (r.tags or [])}
    ingredients = {str(i.get("name", "")).lower() for i in (r.ingredients or []) if isinstance(i, dict)}
    avoid_tag_hits = [t for t in avoid_tags if str(t).lower() in tags]
    avoid_ing_hits = [i for i in avoid_ingredients if str(i).lower() in ingredients]
    hits = avoid_tag_hits + avoid_ing_hits
    penalty = min(0.45, len(hits) * 0.18)
    return penalty, [("AVOID_DOWNRANK", {"item": h}) for h in hits[:2]]


# ---- 兼容旧接口 ----
async def match_recipes(db, ingredients, constraints=None, user_prefs=None):
    return await recommend(db, ingredients, constraints or {}, user_prefs or [])
