from sqlalchemy import Column, String, Integer, DateTime, JSON, func
from app.core.database import Base


class Recipe(Base):
    """菜谱 ORM。注意：ingredients/tags/steps 用 JSON 是 MVP 简化方案。
    数据量上来后应拆为 recipe_ingredients / recipe_tags / recipe_steps 独立表。"""
    __tablename__ = "recipes"

    id = Column(String(32), primary_key=True)
    title = Column(String(100), nullable=False)
    steps = Column(JSON, default=list)
    ingredients = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    cook_time = Column(Integer, default=30)
    calories = Column(Integer, default=300)
    protein = Column(Integer, default=20)
    carbs = Column(Integer, default=30)
    fat = Column(Integer, default=15)
    difficulty = Column(String(10), default="medium")
    source = Column(String(20), default="seed")          # seed / ai_gen / manual / foodkg
    schema_version = Column(Integer, default=1)          # 结构版本，迁移用
    created_at = Column(DateTime, default=func.now())
