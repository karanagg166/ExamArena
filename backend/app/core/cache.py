from typing import Any
import json
from app.core.redis import get_redis


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    redis = get_redis()
    serialized = json.dumps(value)
    if ttl:
        await redis.setex(key, ttl, serialized)
    else:
        await redis.set(key, serialized)


async def cache_get(key: str) -> Any | None:
    redis = get_redis()
    data = await redis.get(key)
    if data is None:
        return None
    return json.loads(data)


async def cache_delete(key: str) -> None:
    redis = get_redis()
    await redis.delete(key)


async def cache_exists(key: str) -> bool:
    redis = get_redis()
    return await redis.exists(key) > 0