import json, os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.recipe import Recipe

SEED_FILE = os.path.join(os.path.dirname(__file__), "recipes.json")


async def seed(db: AsyncSession):
    r = await db.execute(select(Recipe.id).limit(1))
    if r.scalar_one_or_none():
        return  # 已 seed 过，跳过

    with open(SEED_FILE) as f:
        data = json.load(f)

    for item in data:
        db.add(Recipe(**item))
    await db.commit()
