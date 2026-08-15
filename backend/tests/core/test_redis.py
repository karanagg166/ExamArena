from unittest.mock import AsyncMock, patch

import httpx
import pytest

import app.core.redis as redis_module
from app.core.redis import (
    InMemoryRedisFallback,
    UpstashRedisRESTClient,
    connect_redis,
    disconnect_redis,
    get_redis,
)


@pytest.mark.asyncio
async def test_in_memory_redis_fallback_operations():
    client = InMemoryRedisFallback()

    # Ping
    assert await client.ping() is True

    # Set & Get
    assert await client.set("key1", "val1") is True
    assert await client.get("key1") == "val1"
    assert await client.get("nonexistent") is None

    # Setex
    assert await client.setex("key2", 60, "val2") is True
    assert await client.get("key2") == "val2"

    # Exists
    assert await client.exists("key1", "key2", "key3") == 2
    assert await client.exists() == 0

    # Delete
    assert await client.delete("key1", "key3") == 1
    assert await client.get("key1") is None
    assert await client.delete() == 0

    # Aclose
    await client.aclose()


@pytest.mark.asyncio
async def test_upstash_redis_rest_client():
    client = UpstashRedisRESTClient("https://fake-upstash.io", "fake-token")

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        # Mock PING
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.raise_for_status = lambda: None
        mock_resp.json = lambda: {"result": "PONG"}
        mock_post.return_value = mock_resp

        assert await client.ping() is True

        # Mock GET
        mock_resp.json = lambda: {"result": "hello"}
        assert await client.get("foo") == "hello"

        # Mock SET
        mock_resp.json = lambda: {"result": "OK"}
        assert await client.set("foo", "bar", ex=100) is True
        assert await client.setex("foo", 100, "bar") is True

        # Mock EXISTS
        mock_resp.json = lambda: {"result": 1}
        assert await client.exists("foo") == 1
        assert await client.exists() == 0

        # Mock DEL
        mock_resp.json = lambda: {"result": 1}
        assert await client.delete("foo") == 1
        assert await client.delete() == 0

        # Mock Error
        mock_resp.json = lambda: {"error": "Unauthorized"}
        with pytest.raises(RuntimeError, match="Upstash Error"):
            await client.get("error_key")

    await client.aclose()


@pytest.mark.asyncio
async def test_connect_and_disconnect_redis_fallback():
    # Test falling back to in-memory when no remote redis is reachable
    with patch("app.core.redis.settings") as mock_settings:
        mock_settings.UPSTASH_REDIS_REST_URL = None
        mock_settings.UPSTASH_REDIS_REST_TOKEN = None
        mock_settings.REDIS_URL = None
        mock_settings.ENVIRONMENT = "test"

        await connect_redis()
        client = get_redis()
        assert isinstance(client, InMemoryRedisFallback)
        assert await client.ping() is True

        await disconnect_redis()


def test_get_redis_uninitialized():
    old_client = redis_module.redis_client
    try:
        redis_module.redis_client = None
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            get_redis()
    finally:
        redis_module.redis_client = old_client
