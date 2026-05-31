"""Provider 抽象接口层。Agent 只依赖这些接口，不依赖具体 service 实现。
后期替换 GraphRAG / LangGraph / 微服务只需新增 provider 子类。"""

from typing import Protocol


class SenseProvider(Protocol):
    async def __call__(self, image_url: str) -> dict | None: ...


class DecisionProvider(Protocol):
    async def __call__(self, ingredients: list[str], constraints: dict, prefs: list[str]) -> list[dict]: ...


class TaskProvider(Protocol):
    async def __call__(self, recipe_ids: list[str]) -> list[dict]: ...
