import json
import hashlib
import logging
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("cache")

TTL = 600  # 10分钟


async def _get_redis():
    return aioredis.Redis.from_url(settings.redis_url, decode_responses=True)


async def get(key: str) -> dict | None:
    try:
        r = await _get_redis()
        val = await r.get(key)
        await r.close()
        return json.loads(val) if val else None
    except Exception as e:
        logger.debug("cache_get_failed key=%s error=%s", key, e)
        return None


async def set(key: str, data: dict, ttl: int = TTL):
    try:
        r = await _get_redis()
        await r.setex(key, ttl, json.dumps(data, ensure_ascii=False))
        await r.close()
    except Exception as e:
        logger.debug("cache_set_failed key=%s error=%s", key, e)


def make_key(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return "bs:" + hashlib.md5(raw.encode()).hexdigest()[:12]
