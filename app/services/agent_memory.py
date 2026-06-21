"""
Agent MemoryContext 服务：组装四层记忆上下文（会话/偏好/事实/纠错）。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import feedback as feedback_svc
from app.services import inventory as inventory_svc
from app.services import meal_memory
from app.services import correction_logs as correction_svc


async def build_memory_context(
    db: AsyncSession,
    user_id: str | None,
    previous_state: dict | None = None,
    goal: str = "",
) -> dict:
    """组装四层 MemoryContext，即使未登录也返回安全空结构。"""
    ctx = {
        "conversation_memory": {
            "last_ingredients": [],
            "last_recipes": [],
            "last_user_goal": goal or "",
        },
        "preference_memory": {
            "liked_tags": [],
            "avoid_tags": [],
            "liked_ingredients": [],
            "avoid_ingredients": [],
        },
        "fact_memory": {
            "inventory": [],
            "today_nutrition_gap": {},
            "planned_meals": [],
        },
        "correction_memory": {
            "recent_aliases": [],
        },
    }

    # 会话记忆：从上一轮状态继承
    if previous_state:
        ctx["conversation_memory"]["last_ingredients"] = previous_state.get("ingredients", [])[:8]
        ctx["conversation_memory"]["last_recipes"] = [
            r.get("title", "") for r in previous_state.get("recipes", [])[:3]
        ]
        ctx["conversation_memory"]["last_user_goal"] = (
            previous_state.get("intent", {}).get("goal") or goal or ""
        )

    if not user_id:
        return ctx

    # 偏好记忆
    try:
        signals = await feedback_svc.get_preference_signals(db, user_id)
        ctx["preference_memory"] = {
            "liked_tags": signals.get("liked_tags", [])[:8],
            "avoid_tags": signals.get("avoid_tags", [])[:8],
            "liked_ingredients": signals.get("liked_ingredients", [])[:8],
            "avoid_ingredients": signals.get("avoid_ingredients", [])[:8],
        }
    except Exception:
        pass

    # 事实状态记忆：库存
    try:
        items = await inventory_svc.current_inventory(db, user_id)
        ctx["fact_memory"]["inventory"] = items[:10]
    except Exception:
        pass

    # 事实状态记忆：今日餐食 + 营养缺口
    try:
        meals = await meal_memory.today_meals(db, user_id)
        ctx["fact_memory"]["planned_meals"] = meals[:5]
    except Exception:
        pass

    try:
        summary = await meal_memory.nutrition_summary(db, user_id, "day")
        if summary:
            targets = summary.get("targets", {})
            totals = summary.get("totals", {})
            ctx["fact_memory"]["today_nutrition_gap"] = {
                k: round(targets.get(k, 0) - totals.get(k, 0), 1)
                for k in ["calories", "protein", "carbs", "fat"]
            }
    except Exception:
        pass

    # 纠错记忆
    try:
        aliases = await correction_svc.get_recent_aliases(db, user_id, limit=20)
        ctx["correction_memory"]["recent_aliases"] = aliases
    except Exception:
        pass

    return ctx


def build_memory_used(memory_context: dict) -> list[dict]:
    """从 memory_context 生成 memory_used 摘要列表。
    格式: [{type, key, summary}] — type 为 conversation/preference/fact/correction。
    """
    used: list[dict] = []

    conv = memory_context.get("conversation_memory", {})
    if conv.get("last_ingredients"):
        used.append({
            "type": "conversation",
            "key": "last_ingredients",
            "summary": f"沿用了上一轮识别到的{', '.join(conv['last_ingredients'][:4])}",
        })
    if conv.get("last_user_goal") and conv["last_user_goal"] != "balanced":
        goal_labels = {"fat_loss": "减脂", "muscle_gain": "增肌"}
        label = goal_labels.get(conv["last_user_goal"], conv["last_user_goal"])
        used.append({
            "type": "conversation",
            "key": "health_goal",
            "summary": f"参考了{label}目标",
        })

    pref = memory_context.get("preference_memory", {})
    if pref.get("liked_tags"):
        used.append({
            "type": "preference",
            "key": "liked_tags",
            "summary": f"偏好口味: {', '.join(pref['liked_tags'][:4])}",
        })
    if pref.get("avoid_tags"):
        used.append({
            "type": "preference",
            "key": "avoid_tags",
            "summary": f"避开了不喜欢的 {', '.join(pref['avoid_tags'][:4])}",
        })
    if pref.get("liked_ingredients"):
        used.append({
            "type": "preference",
            "key": "liked_ingredients",
            "summary": f"喜好食材: {', '.join(pref['liked_ingredients'][:4])}",
        })

    fact = memory_context.get("fact_memory", {})
    inv = fact.get("inventory", [])
    if inv:
        used.append({
            "type": "fact",
            "key": "available_items",
            "summary": f"读取当前库存 {len(inv)} 项",
        })
    gap = fact.get("today_nutrition_gap", {})
    if gap and gap.get("calories", 0) > 0:
        used.append({
            "type": "fact",
            "key": "nutrition_gap",
            "summary": f"今日还需摄入 {gap.get('calories', 0):.0f} 千卡",
        })

    corr = memory_context.get("correction_memory", {})
    aliases = corr.get("recent_aliases", [])
    if aliases:
        used.append({
            "type": "correction",
            "key": "recent_aliases",
            "summary": f"参考了 {len(aliases)} 条历史纠错记录",
        })

    return used
