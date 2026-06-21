from sqlalchemy import Column, String, Integer, Date, DateTime, JSON, ForeignKey, UniqueConstraint, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True)
    openid = Column(String(64), unique=True, nullable=True, index=True)  # v5: 兼容旧 OpenID 演示登录，密码注册可为空
    phone = Column(String(20), default="")
    name = Column(String(50), default="")
    avatar_url = Column(String(2000), default="")
    username = Column(String(64), unique=True, nullable=True, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(128), default="")
    auth_provider = Column(String(30), default="openid")  # openid / password
    status = Column(String(20), default="active")          # active / disabled
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(String(32), ForeignKey("users.id"), primary_key=True)
    goal = Column(String(30), default="")
    preferences = Column(JSON, default=list)
    body_metrics = Column(JSON, default=dict)
    nutrition_targets = Column(JSON, default=dict)
    health_score = Column(Integer, default=60)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    deficits = Column(JSON, default=list)
    recorded_at = Column(Date, nullable=False, default=func.current_date(), index=True)


class IngredientInventory(Base):
    __tablename__ = "ingredient_inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(80), nullable=False, index=True)
    amount = Column(Integer, nullable=True)
    unit = Column(String(20), default="")
    source = Column(String(30), default="manual")
    freshness = Column(String(30), default="")
    confidence = Column(Integer, default=0)
    meta = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class MealRecord(Base):
    __tablename__ = "meal_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    meal_slot = Column(String(20), default="lunch", index=True)
    status = Column(String(20), default="planned", index=True)
    recipe_id = Column(String(64), default="")
    recipe_snapshot = Column(JSON, default=dict)
    ingredients_used = Column(JSON, default=list)
    shopping_list = Column(JSON, default=list)
    nutrition = Column(JSON, default=dict)
    planned_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    recipe_id = Column(String(32), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())


class PreferenceMemory(Base):
    __tablename__ = "preference_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    recipe_id = Column(String(32), default="", index=True)
    rating = Column(Integer, default=0)
    comment = Column(String(500), default="")
    parsed = Column(JSON, default=dict)
    weight = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())


class RecipeFavorite(Base):
    __tablename__ = "recipe_favorites"
    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id", name="uq_recipe_favorite_user_target"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    target_type = Column(String(30), nullable=False, index=True)
    target_id = Column(String(64), nullable=False, index=True)
    snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    content = Column(String(2000), default="")
    category = Column(String(30), default="recipe", index=True)
    images = Column(JSON, default=list)
    recipe_payload = Column(JSON, default=dict)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=func.now())


class CommunityLike(Base):
    __tablename__ = "community_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_community_like_post_user"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())


class CorrectionLog(Base):
    """用户对识别结果的纠错记录，用于后续优化同义词和识别后处理。"""
    __tablename__ = "correction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    source = Column(String(20), default="sense", comment="sense/inventory")
    original_name = Column(String(100), default="")
    corrected_name = Column(String(100), default="")
    action = Column(String(20), nullable=False, comment="rename/delete/merge/weight_adjust")
    confidence = Column(Integer, default=0, comment="原始置信度*100")
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
