import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import User, Profile, NutritionLog


def _uid():
    return "u_" + uuid.uuid4().hex[:16]


async def create_user(db: AsyncSession, openid: str, phone: str = "", name: str = "") -> User:
    user = User(id=_uid(), openid=openid, phone=phone, name=name)
    db.add(user)
    await db.flush()
    profile = Profile(user_id=user.id)
    db.add(profile)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(user)
    return user


async def get_user_by_openid(db: AsyncSession, openid: str) -> User | None:
    r = await db.execute(select(User).where(User.openid == openid))
    return r.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    r = await db.execute(select(User).where(User.id == user_id))
    return r.scalar_one_or_none()


async def get_profile(db: AsyncSession, user_id: str) -> dict | None:
    r = await db.execute(
        select(User.name, Profile.goal, Profile.preferences, Profile.health_score)
        .join(Profile, User.id == Profile.user_id)
        .where(User.id == user_id)
    )
    row = r.one_or_none()
    if row is None:
        return None
    return {
        "user_id": user_id,
        "name": row.name or "",
        "goal": row.goal or "",
        "preferences": row.preferences or [],
        "health_score": row.health_score or 60,
    }


async def update_profile(db: AsyncSession, user_id: str, goal: str | None = None, preferences: list | None = None):
    vals = {}
    if goal is not None:
        vals["goal"] = goal
    if preferences is not None:
        vals["preferences"] = preferences
    if vals:
        await db.execute(update(Profile).where(Profile.user_id == user_id).values(**vals))
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def get_nutrition_status(db: AsyncSession, user_id: str) -> dict:
    r = await db.execute(
        select(NutritionLog).where(NutritionLog.user_id == user_id).order_by(NutritionLog.recorded_at.desc()).limit(1)
    )
    log = r.scalar_one_or_none()
    if log is None:
        return {"score": 0, "deficits": []}
    return {"score": log.score, "deficits": log.deficits or []}
