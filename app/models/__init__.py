from sqlalchemy import Column, String, Integer, Date, DateTime, JSON, ForeignKey, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True)
    openid = Column(String(64), unique=True, nullable=False, index=True)
    phone = Column(String(20), default="")
    name = Column(String(50), default="")
    created_at = Column(DateTime, default=func.now())


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(String(32), ForeignKey("users.id"), primary_key=True)
    goal = Column(String(30), default="")
    preferences = Column(JSON, default=list)
    health_score = Column(Integer, default=60)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    deficits = Column(JSON, default=list)
    recorded_at = Column(Date, nullable=False, default=func.current_date(), index=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    recipe_id = Column(String(32), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
