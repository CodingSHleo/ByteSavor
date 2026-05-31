import redis.asyncio as aioredis
from app.core.config import settings

pool = aioredis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)


async def get_redis():
    client = aioredis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()
