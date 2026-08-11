"""Shared fixed-window request limiting with a development fallback."""

from __future__ import annotations

import asyncio
import time

from redis.asyncio import Redis

from app.core.logging import get_logger

logger = get_logger(__name__)

_INCREMENT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


class SharedRateLimiter:
    """Count requests in Redis so every API process enforces the same limit."""

    def __init__(self, *, limit: int, redis_url: str | None) -> None:
        self._limit = max(1, limit)
        self._redis = Redis.from_url(redis_url, decode_responses=True) if redis_url else None
        self._fallback_counts: dict[tuple[int, str], int] = {}
        self._fallback_lock = asyncio.Lock()
        self._redis_warning_logged = False

    async def allow(self, client_key: str) -> bool:
        bucket = int(time.time() // 60)
        if self._redis is not None:
            try:
                key = f"cla:request-limit:{bucket}:{client_key}"
                count = int(await self._redis.eval(_INCREMENT_SCRIPT, 1, key, 70))
                return count <= self._limit
            except Exception:  # noqa: BLE001 - degraded service should stay available
                if not self._redis_warning_logged:
                    logger.exception("Redis rate limiter unavailable; using process-local fallback")
                    self._redis_warning_logged = True
        return await self._allow_fallback(bucket, client_key)

    async def _allow_fallback(self, bucket: int, client_key: str) -> bool:
        async with self._fallback_lock:
            stale = [key for key in self._fallback_counts if key[0] < bucket]
            for key in stale:
                del self._fallback_counts[key]
            key = (bucket, client_key)
            count = self._fallback_counts.get(key, 0) + 1
            self._fallback_counts[key] = count
            return count <= self._limit

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
