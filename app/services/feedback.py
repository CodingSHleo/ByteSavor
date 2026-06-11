from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Feedback
from app.models.recipe import Recipe
from app.services.user import update_profile, get_profile


async def submit_feedback(db: AsyncSession, user_id: str, recipe_id: str, rating: int) -> dict:
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
        r = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
        recipe = r.scalar_one_or_none()
        if recipe:
            profile = await get_profile(db, user_id)
            prefs = list(profile.get("preferences", []) if profile else [])
            tags = [t for t in recipe.tags if not t.startswith("quick")]

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
