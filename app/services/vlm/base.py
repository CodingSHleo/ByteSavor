from abc import ABC, abstractmethod


class BaseVLMProvider(ABC):
    """VLM provider 抽象基类。换模型只需新增子类，router 不用动。"""

    @abstractmethod
    async def analyze_food(self, image_url: str, prompt: str) -> dict | None:
        """识别图片中的食材，返回 {ingredients: [...], portion_estimation: {...}}，失败返回 None"""
        ...
