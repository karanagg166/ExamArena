"""
Attempt Cache — Redis caching layer for student exam attempt data.

Caches in-progress attempt state to reduce DB reads during active exams.
"""

import json
import logging
from typing import Any

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

ATTEMPT_CACHE_TTL = 60 * 60  # 1 hour


async def cache_attempt(attempt_id: str, data: dict[str, Any]) -> None:
    """Store attempt data in Redis."""
    redis = get_redis()
    key = f"attempt:{attempt_id}"
    await redis.setex(key, ATTEMPT_CACHE_TTL, json.dumps(data, default=str))


async def get_cached_attempt(attempt_id: str) -> dict[str, Any] | None:
    """Retrieve cached attempt data from Redis."""
    redis = get_redis()
    key = f"attempt:{attempt_id}"
    raw = await redis.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def invalidate_attempt_cache(attempt_id: str) -> None:
    """Delete cached attempt data (e.g., on submit)."""
    redis = get_redis()
    key = f"attempt:{attempt_id}"
    await redis.delete(key)
