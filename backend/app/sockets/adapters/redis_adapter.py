"""Redis pub/sub adapter for distributed WebSocket broadcasting."""

import json
import logging
from typing import Any

from app.core.redis import get_redis, redis_client

logger = logging.getLogger(__name__)


class RedisSocketAdapter:
    """Provides pub/sub distribution for WebSocket events."""

    def __init__(self, channel_prefix: str = "exam_arena:ws:") -> None:
        self.prefix = channel_prefix

    async def publish(self, room: str, message: dict[str, Any]) -> None:
        """Publishes a socket message to a Redis room channel if connected."""
        if not redis_client:
            return

        channel = f"{self.prefix}{room}"
        payload = json.dumps(message)
        try:
            client = get_redis()
            # If standard TCP redis client supports publish
            if hasattr(client, "publish"):
                await client.publish(channel, payload)
        except Exception as e:
            logger.debug("Redis pub/sub publish skipped: %s", e)


redis_adapter = RedisSocketAdapter()
