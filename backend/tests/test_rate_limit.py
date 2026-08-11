"""Tests for shared request limiting behavior."""

import asyncio

from app.infrastructure.rate_limit import SharedRateLimiter


def test_in_memory_fallback_enforces_limit_per_client() -> None:
    async def exercise() -> None:
        limiter = SharedRateLimiter(limit=2, redis_url=None)
        assert await limiter.allow("client-a") is True
        assert await limiter.allow("client-a") is True
        assert await limiter.allow("client-a") is False
        assert await limiter.allow("client-b") is True
        await limiter.close()

    asyncio.run(exercise())
