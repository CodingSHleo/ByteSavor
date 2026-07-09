import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import User, Profile, NutritionLog

DEFAULT_BODY_METRICS = {
    "sex": "male",
    "age": 22,
    "height_cm": 175,
    "weight_kg": 70,
    "exercise_per_week": 3,
}


def _num(value, default):
    try:
        n = float(value)
        return n if n > 0 else default
    except Exception:
        return default


def calculate_nutrition_targets(goal: str = "balanced", body_metrics: dict | None = None, custom_targets: dict | None = None) -> dict:
    metrics = {**DEFAULT_BODY_METRICS, **(body_metrics or {})}
    sex = metrics.get("sex") or "male"
    age = _num(metrics.get("age"), DEFAULT_BODY_METRICS["age"])
    height = _num(metrics.get("height_cm"), DEFAULT_BODY_METRICS["height_cm"])
    weight = _num(metrics.get("weight_kg"), DEFAULT_BODY_METRICS["weight_kg"])
    exercise = _num(metrics.get("exercise_per_week"), DEFAULT_BODY_METRICS["exercise_per_week"])

    bmr = 10 * weight + 6.25 * height - 5 * age + (5 if sex == "male" else -161)
    activity = 1.2
    if exercise >= 6:
        activity = 1.725
    elif exercise >= 4:
        activity = 1.55
    elif exercise >= 2:
        activity = 1.375
    maintenance = bmr * activity

    if goal == "fat_loss":
        calories = maintenance * 0.82
        protein_per_kg = 1.8
        fat_ratio = 0.25
    elif goal == "muscle_gain":
        calories = maintenance * 1.12
        protein_per_kg = 2.0
        fat_ratio = 0.25
    else:
        calories = maintenance
        protein_per_kg = 1.4
        fat_ratio = 0.28

    protein = weight * protein_per_kg
    fat = calories * fat_ratio / 9
    carbs = max(0, (calories - protein * 4 - fat * 9) / 4)
    targets = {
        "calories": int(round(calories)),
        "protein": int(round(protein)),
        "carbs": int(round(carbs)),
        "fat": int(round(fat)),
        "fiber": 30 if calories >= 1800 else 25,
        "vitamin_c": 90,
        "iron": 18 if sex == "female" else 8,
        "source": "calculated",
    }

    for key, value in (custom_targets or {}).items():
        if key in targets and value not in ("", None):
            targets[key] = _num(value, targets[key])
            if key != "source":
                targets[key] = int(round(targets[key]))
    if custom_targets:
        targets["source"] = "custom"
    return targets


def _uid():
    return "u_" + uuid.uuid4().hex[:16]


async def ensure_profile_columns(db: AsyncSession) -> None:
    conn = await db.connection()
    for column in ("body_metrics", "nutrition_targets"):
        result = await conn.exec_driver_sql(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'profiles' AND COLUMN_NAME = %s",
            (column,),
        )
        if not result.scalar():
            await conn.exec_driver_sql(f"ALTER TABLE profiles ADD COLUMN {column} JSON NULL")


async def create_user(db: AsyncSession, openid: str, phone: str = "", name: str = "") -> User:
    await ensure_profile_columns(db)
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


# ── v5: 用户表字段补齐 ──
async def ensure_user_auth_columns(db: AsyncSession) -> None:
    """补齐 User 表账号与展示字段。"""
    columns = {
        "avatar_url": "VARCHAR(2000) DEFAULT ''",
        "username": "VARCHAR(64) NULL",
        "email": "VARCHAR(120) NULL",
        "password_hash": "VARCHAR(128) DEFAULT ''",
        "auth_provider": "VARCHAR(30) DEFAULT 'openid'",
        "status": "VARCHAR(20) DEFAULT 'active'",
        "last_login_at": "DATETIME NULL",
        "role": "VARCHAR(20) DEFAULT 'user'",
    }
    conn = await db.connection()
    for col_name in columns:
        result = await conn.exec_driver_sql(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = %s",
            (col_name,),
        )
        if not result.scalar():
            col_def = columns[col_name]
            await conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

    openid_nullable = await conn.exec_driver_sql(
        "SELECT IS_NULLABLE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'openid'"
    )
    if openid_nullable.scalar() == "NO":
        await conn.exec_driver_sql("ALTER TABLE users MODIFY COLUMN openid VARCHAR(64) NULL")

    for index_name, col_name in (
        ("uq_users_username", "username"),
        ("uq_users_email", "email"),
    ):
        index_exists = await conn.exec_driver_sql(
            "SELECT COUNT(*) FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = %s",
            (index_name,),
        )
        if not index_exists.scalar():
            await conn.exec_driver_sql(f"CREATE UNIQUE INDEX {index_name} ON users ({col_name})")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """校验密码强度。返回 (通过, 错误信息)。"""
    if not password or len(password) < 8:
        return False, "密码长度至少 8 位"
    if not any(c.isupper() for c in password):
        return False, "密码需要至少一个大写字母"
    if not any(c.islower() for c in password):
        return False, "密码需要至少一个小写字母"
    if not any(c.isdigit() for c in password):
        return False, "密码需要至少一个数字"
    return True, ""


def validate_username_format(username: str) -> bool:
    """校验用户名格式：3-32 位，字母数字下划线短横线。"""
    import re
    name = (username or "").strip()
    return bool(re.match(r"^[A-Za-z0-9_-]{3,32}$", name))


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    name = (username or "").strip().lower()
    r = await db.execute(select(User).where(User.username == name))
    return r.scalar_one_or_none()


async def create_password_user(
    db: AsyncSession,
    username: str,
    password: str,
    name: str = "",
    email: str = "",
    role: str = "user",
) -> User:
    """密码注册：bcrypt 哈希密码，auth_provider='password'。"""
    from app.core.security import hash_password
    name_lower = (username or "").strip().lower()
    user = User(
        id=_uid(),
        username=name_lower,
        name=name.strip() or name_lower,
        password_hash=hash_password(password),
        auth_provider="password",
        email=(email or "").strip() or None,
        role=role,
    )
    db.add(user)
    await db.flush()
    # 创建 profile
    profile = Profile(user_id=user.id)
    db.add(profile)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(user)
    return user


async def authenticate_password_user(db: AsyncSession, username: str, password: str) -> User | None:
    """密码登录：查找用户并验证密码。返回 User 或 None。"""
    from app.core.security import verify_password
    user = await get_user_by_username(db, username)
    if user is None:
        return None
    if not user.password_hash:
        return None
    try:
        password_ok = verify_password(password, user.password_hash)
    except ValueError:
        return None
    if not password_ok:
        return None
    # 更新 last_login_at
    from datetime import datetime
    user.last_login_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def get_profile(db: AsyncSession, user_id: str) -> dict | None:
    await ensure_profile_columns(db)
    r = await db.execute(
        select(User.name, User.avatar_url, Profile.goal, Profile.preferences, Profile.body_metrics, Profile.nutrition_targets, Profile.health_score)
        .join(Profile, User.id == Profile.user_id)
        .where(User.id == user_id)
    )
    row = r.one_or_none()
    if row is None:
        return None
    body_metrics = row.body_metrics or DEFAULT_BODY_METRICS
    custom_targets = row.nutrition_targets or {}
    goal = row.goal or "balanced"
    return {
        "user_id": user_id,
        "name": row.name or "",
        "avatar_url": row.avatar_url or "",
        "goal": goal,
        "preferences": row.preferences or [],
        "body_metrics": body_metrics,
        "nutrition_targets": custom_targets,
        "computed_targets": calculate_nutrition_targets(goal, body_metrics, custom_targets),
        "health_score": row.health_score or 60,
    }


async def update_profile(
    db: AsyncSession,
    user_id: str,
    name: str | None = None,
    avatar_url: str | None = None,
    goal: str | None = None,
    preferences: list | None = None,
    body_metrics: dict | None = None,
    nutrition_targets: dict | None = None,
):
    await ensure_profile_columns(db)
    await ensure_user_auth_columns(db)
    user_vals = {}
    if name is not None:
        user_vals["name"] = str(name or "").strip()[:50]
    if avatar_url is not None:
        user_vals["avatar_url"] = str(avatar_url or "").strip()
    if user_vals:
        await db.execute(update(User).where(User.id == user_id).values(**user_vals))
    vals = {}
    if goal is not None:
        vals["goal"] = goal
    if preferences is not None:
        vals["preferences"] = preferences
    if body_metrics is not None:
        vals["body_metrics"] = body_metrics
    if nutrition_targets is not None:
        vals["nutrition_targets"] = nutrition_targets
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
