import redis.asyncio as aioredis
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class UpstashRedisRESTClient:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=5.0)
        print("⚡ Initialized UpstashRedisRESTClient")

    async def _execute(self, payload: list) -> any:
        try:
            response = await self.client.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"Upstash Error: {data['error']}")
            return data.get("result")
        except Exception as e:
            logger.error(f"Upstash execution error: {e}")
            raise e

    async def get(self, key: str) -> str | None:
        return await self._execute(["GET", key])

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        cmd = ["SET", key, str(value)]
        if ex is not None:
            cmd.extend(["EX", str(ex)])
        res = await self._execute(cmd)
        return res == "OK"

    async def setex(self, name: str, time: int, value: str) -> bool:
        res = await self._execute(["SET", name, str(value), "EX", str(time)])
        return res == "OK"

    async def delete(self, *names: str) -> int:
        if not names:
            return 0
        res = await self._execute(["DEL", *names])
        return int(res) if res is not None else 0

    async def exists(self, *names: str) -> int:
        if not names:
            return 0
        res = await self._execute(["EXISTS", *names])
        return int(res) if res is not None else 0

    async def ping(self) -> bool:
        res = await self._execute(["PING"])
        return res == "PONG"

    async def aclose(self) -> None:
        await self.client.aclose()
        print("🔌 UpstashRedisRESTClient closed")


class InMemoryRedisFallback:
    def __init__(self):
        self._store = {}
        print("💾 Initialized InMemoryRedisFallback cache")

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._store[key] = str(value)
        return True

    async def setex(self, name: str, time: int, value: str) -> bool:
        self._store[name] = str(value)
        return True

    async def delete(self, *names: str) -> int:
        count = 0
        for name in names:
            if name in self._store:
                del self._store[name]
                count += 1
        return count

    async def exists(self, *names: str) -> int:
        count = 0
        for name in names:
            if name in self._store:
                count += 1
        return count

    async def aclose(self) -> None:
        pass

    async def ping(self) -> bool:
        return True


redis_client: aioredis.Redis | UpstashRedisRESTClient | InMemoryRedisFallback | None = None


async def connect_redis() -> None:
    global redis_client
    # 1. Prioritize Upstash Redis REST Client if configured
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        try:
            client = UpstashRedisRESTClient(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN,
            )
            await client.ping()
            redis_client = client
            print("✅ Upstash Redis REST client connected successfully")
            return
        except Exception as e:
            print(f"⚠️ Upstash Redis REST client failed to connect: {e}")

    # 2. Fall back to standard TCP Redis if configured
    if settings.REDIS_URL:
        try:
            if settings.ENVIRONMENT == "production" and "localhost" in settings.REDIS_URL:
                raise ConnectionError("Local Redis URL ignored in production environment")

            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            await client.ping()
            redis_client = client
            print("✅ TCP Redis connected successfully")
            return
        except Exception as e:
            print(f"⚠️ TCP Redis connection failed: {e}")

    # 3. Last fallback: InMemory
    print("💾 Falling back to InMemoryRedisFallback.")
    redis_client = InMemoryRedisFallback()


async def disconnect_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()
        print("🔌 Redis connection closed")


def get_redis() -> aioredis.Redis | UpstashRedisRESTClient | InMemoryRedisFallback:
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client