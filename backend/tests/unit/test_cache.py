import pytest

from app.core.redis import InMemoryRedisFallback


class TestInMemoryRedisFallback:
    """U48-U51: Tests for in-memory Redis fallback cache implementation."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        cache = InMemoryRedisFallback()
        ok = await cache.set("test_key", "test_value")
        assert ok is True

        val = await cache.get("test_key")
        assert val == "test_value"

    @pytest.mark.asyncio
    async def test_get_non_existent(self):
        cache = InMemoryRedisFallback()
        val = await cache.get("non_existent_key")
        assert val is None

    @pytest.mark.asyncio
    async def test_setex(self):
        cache = InMemoryRedisFallback()
        ok = await cache.setex("expiring_key", 60, "temp_value")
        assert ok is True
        assert await cache.get("expiring_key") == "temp_value"

    @pytest.mark.asyncio
    async def test_delete(self):
        cache = InMemoryRedisFallback()
        await cache.set("k1", "v1")
        await cache.set("k2", "v2")

        count = await cache.delete("k1")
        assert count == 1
        assert await cache.get("k1") is None
        assert await cache.get("k2") == "v2"

    @pytest.mark.asyncio
    async def test_exists(self):
        cache = InMemoryRedisFallback()
        await cache.set("existing", "1")

        assert await cache.exists("existing") == 1
        assert await cache.exists("non_existing") == 0

    @pytest.mark.asyncio
    async def test_ping(self):
        cache = InMemoryRedisFallback()
        assert await cache.ping() is True
