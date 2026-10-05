"""
Token Blacklist — Redis-backed JWT invalidation.

When a user logs out, their token's JTI (JWT ID) is stored in Redis
until the token naturally expires. The `get_current_user` dependency
checks this blacklist before authorizing requests.

Security Policy: Fail Closed.
If the token contains a JTI and the blacklist cannot be verified due to
Redis unavailability or network error, requests are rejected with
HTTP 503 Service Unavailable rather than silently accepting potentially
revoked tokens.
"""

import logging

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class TokenBlacklistUnavailableError(Exception):
    """Raised when token blacklist service (Redis) cannot be reached or fails."""


async def blacklist_token(jti: str, expires_in_seconds: int) -> None:
    """Add a token's JTI to the Redis blacklist with a TTL matching its expiry."""
    try:
        redis = get_redis()
        key = f"blacklist:jti:{jti}"
        await redis.setex(key, expires_in_seconds, "1")
        logger.info(f"Token {jti} blacklisted for {expires_in_seconds}s")
    except Exception as e:
        logger.warning(f"Failed to blacklist token {jti}: {e}")
        raise TokenBlacklistUnavailableError(
            "Blacklist service unavailable"
        ) from e


async def is_token_blacklisted(jti: str) -> bool:
    """Return True if the token's JTI has been blacklisted (user logged out).

    Fails closed: if the blacklist backend (Redis) is unreachable or errors,
    raises TokenBlacklistUnavailableError so that callers do not authenticate
    potentially revoked tokens.
    """
    try:
        redis = get_redis()
        key = f"blacklist:jti:{jti}"
        result = await redis.exists(key)
        return result > 0
    except Exception as e:
        logger.warning(f"Failed to check token blacklist for {jti}: {e}")
        raise TokenBlacklistUnavailableError(
            "Blacklist service unavailable"
        ) from e
