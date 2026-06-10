import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe
from app.services.recipe_presenter import recipe_brief

logger = logging.getLogger("decision")


async def recommend(db: AsyncSession, ingredients: list[str], constraints: dict, user_prefs: list[str]) -> list[dict]:
    """推荐 pipeline：检索 → 硬过滤 → 软排序 → 解释生成 → fallback"""
    t0 = time.time()
    taste = constraints.get("taste", "")
    goal = constraints.get("goal", "")
    time_limit = constraints.get("time_limit", 999)
    is_explore = len(ingredients) == 0

    # ---- 1. 候选检索 + SQL层硬过滤 ----
    recipes = await _retrieve(db, time_limit)

    # ---- 2. 硬过滤（已在SQL完成，保留Python层做兜底） ----
    candidates = _hard_filter(recipes, time_limit)

    # ---- 3. 排序 ----
    if is_explore:
        scored = _explore_rank(candidates, taste, goal, user_prefs)
    else:
        scored = _rank(candidates, ingredients, taste, goal, user_prefs)

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
        r["fallback"] = is_fallback
    return result


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
def _rank(recipes: list[Recipe], ingredients: list[str], taste: str, goal: str, prefs: list[str]) -> list[dict]:
    scored = []
    for r in recipes:
        s_ing, codes_ing = _calc_ingredient(r, ingredients)
        s_tag, codes_tag = _calc_tag(r, taste, goal)
        s_pref, codes_pref = _calc_pref(r, prefs)
        s = s_ing * 0.5 + s_tag * 0.3 + s_pref * 0.2
        if s > 0.25:
            scored.append({**recipe_brief(r), "match_score": round(s, 2), "_codes": codes_ing + codes_tag + codes_pref})
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


# ---------- 3b. 探索排序 ----------
def _explore_rank(recipes: list[Recipe], taste: str, goal: str, prefs: list[str]) -> list[dict]:
    scored = []
    for r in recipes:
        s_tag, codes_tag = _calc_tag(r, taste, goal)
        s_pref, codes_pref = _calc_pref(r, prefs)
        s = s_tag * 0.6 + s_pref * 0.4
        codes = codes_tag + codes_pref
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
    "TASTE_MATCH": "口味匹配: {taste}",
    "LOW_CARB": "低碳水",
    "HIGH_PROTEIN_GOAL": "高蛋白适合{goal}",
    "BALANCED": "营养均衡",
    "PREF_MATCH": "符合偏好: {pref}",
    "QUICK": "{time}分钟快速完成",
    "NEAR_FIT": "接近匹配: {title}",
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
    recipe_names = {i["name"].lower() for i in r.ingredients}
    user_set = {u.lower() for u in user_ings}
    exact = recipe_names & user_set
    # 双向覆盖率: 菜谱侧60% + 用户侧40%
    recipe_coverage = len(exact) / len(recipe_names) if recipe_names else 0
    user_coverage = len(exact) / len(user_set) if user_set else 0
    score = min(recipe_coverage * 0.6 + user_coverage * 0.4, 1.0)
    codes = [("ING_MATCH", {"ingredient": e}) for e in exact]
    return score, codes


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
    tags = [t.lower() for t in r.tags]
    hits = [p for p in prefs if p.lower() in tags]
    score = min(0.5 + len(hits) * 0.2, 1.0)
    codes = [("PREF_MATCH", {"pref": h}) for h in hits[:3]]
    return score, codes


# ---- 兼容旧接口 ----
async def match_recipes(db, ingredients, constraints=None, user_prefs=None):
    return await recommend(db, ingredients, constraints or {}, user_prefs or [])
