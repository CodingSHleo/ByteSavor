from app.core.config import settings
from app.services.vlm.openai import OpenAICompatProvider
from app.services.vlm.prompts import FOOD_ANALYSIS

_provider = OpenAICompatProvider(model=settings.vlm_model)


async def analyze_food(image_url: str, prompt: str = FOOD_ANALYSIS) -> dict | None:
    return await _provider.analyze_food(image_url, prompt)
