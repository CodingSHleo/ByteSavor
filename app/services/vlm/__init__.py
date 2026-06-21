import hashlib
import logging
import time

from app.core.cache import get as cache_get, set as cache_set, make_key
from app.core.config import settings
from app.services.food_synonyms import normalize_ingredients
from app.services.nutrition_calculator import calculate_total
from app.services.vlm.openai import OpenAICompatProvider
from app.services.vlm.prompts import FOOD_ANALYSIS, FOOD_ANALYSIS_PROMPT_VERSION

logger = logging.getLogger("vlm")

_provider = OpenAICompatProvider(model=settings.vlm_model)

IMAGE_CACHE_TTL = 1800  # 30 分钟


def _image_hash(image_url: str) -> str:
    """对 image_url 内容 hash（URL 字符串或 base64 数据）。"""
    return hashlib.md5(image_url.encode("utf-8")).hexdigest()[:16]


def _with_observability(result: dict, *, cache_hit: bool, latency_ms: int, cache_key: str, fingerprint: str) -> dict:
    return {
        **result,
        "cache_hit": cache_hit,
        "cache_key": cache_key,
        "latency_ms": latency_ms,
        "model": settings.vlm_model,
        "prompt_version": FOOD_ANALYSIS_PROMPT_VERSION,
        "image_fingerprint": fingerprint,
    }


async def analyze_food(image_url: str, prompt: str = FOOD_ANALYSIS) -> dict | None:
    started = time.perf_counter()
    fingerprint = _image_hash(image_url)
    cache_key = make_key("vlm", settings.vlm_model, FOOD_ANALYSIS_PROMPT_VERSION, fingerprint)
    cached = await cache_get(cache_key)
    if cached:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "vlm_cache_hit key=%s model=%s prompt_version=%s",
            cache_key, settings.vlm_model, FOOD_ANALYSIS_PROMPT_VERSION,
        )
        result = _with_observability(
            cached,
            cache_hit=True,
            latency_ms=latency_ms,
            cache_key=cache_key,
            fingerprint=fingerprint,
        )
        logger.info("vlm_analyze_done cache_hit=true latency_ms=%d", latency_ms)
        return result

    raw = await _provider.analyze_food(image_url, prompt)
    if raw is None:
        return None
    ingredients = raw.get("ingredients", [])
    portion = raw.get("portion_estimation", {})

    # 后处理：同义词标准化 + 低置信标记 + 同名合并
    normalized = normalize_ingredients(ingredients)
    low_conf = [i for i in normalized if i.get("needs_confirm")]
    high_conf = [i for i in normalized if not i.get("needs_confirm")]

    logger.info(
        "vlm_postprocess total=%d high_conf=%d low_conf=%d",
        len(normalized), len(high_conf), len(low_conf),
    )

    # 营养计量
    nutrition_data = calculate_total(normalized)

    analysis_result = {
        "ingredients": normalized,
        "portion_estimation": portion,
        "confidence_summary": {
            "total": len(normalized),
            "high_confidence": len(high_conf),
            "needs_confirm": len(low_conf),
        },
        "nutrition": {
            "per_item": nutrition_data["items"],
            "total": nutrition_data["total_nutrition"],
            "has_unknown": nutrition_data["has_unknown"],
        },
    }

    # 写入缓存
    await cache_set(cache_key, analysis_result, ttl=IMAGE_CACHE_TTL)

    latency_ms = int((time.perf_counter() - started) * 1000)
    logger.info("vlm_analyze_done cache_hit=false latency_ms=%d", latency_ms)
    return _with_observability(
        analysis_result,
        cache_hit=False,
        latency_ms=latency_ms,
        cache_key=cache_key,
        fingerprint=fingerprint,
    )
