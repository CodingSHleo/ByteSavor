from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession


class BaseDecisionEngine(ABC):
    """决策引擎抽象基类。
    当前 MySQL 实现 → 后期 Neo4j/GraphRAG 替换只需新增子类，
    router 和接口契约完全不动。"""

    @abstractmethod
    async def recommend(
        self,
        db: AsyncSession,
        ingredients: list[str],
        constraints: dict,
        user_prefs: list[str],
    ) -> list[dict]:
        ...
