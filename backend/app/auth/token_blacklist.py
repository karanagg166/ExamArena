"""
Token Blacklist — Redis-backed JWT invalidation.

When a user logs out, their token's JTI (JWT ID) is stored in Redis
until the token naturally expires. The `get_current_user` dependency
checks this blacklist before authorizing requests.
"""

import logging
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


async def blacklist_token(jti: str, expires_in_seconds: int) -> None:
    """Add a token's JTI to the Redis blacklist with a TTL matching its expiry."""
    redis = get_redis()
    key = f"blacklist:jti:{jti}"
    await redis.setex(key, expires_in_seconds, "1")
    logger.info(f"Token {jti} blacklisted for {expires_in_seconds}s")


async def is_token_blacklisted(jti: str) -> bool:
    """Return True if the token's JTI has been blacklisted (user logged out)."""
    redis = get_redis()
    key = f"blacklist:jti:{jti}"
    result = await redis.exists(key)
    return result > 0
