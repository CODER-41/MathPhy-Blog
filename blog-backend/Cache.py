"""
Redis cache layer.

Design decisions:
  - fastapi-cache2 handles @cache decorator + RedisBackend
  - Manual invalidation uses SCAN+DEL by pattern (avoids storing separate key sets)
  - Rate limiting uses Redis INCR + EXPIRE (sliding window per IP)
  - Fail-open: if Redis is down, cache misses go to DB and rate limits are skipped
"""
import logging
import redis.asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache  # re-exported so routes import from here
from app.core.config import settings

logger = logging.getLogger(__name__)

__all__ = ["cache", "init_cache", "close_cache",
           "invalidate_post", "invalidate_lists",
           "invalidate_taxonomy", "invalidate_comments",
           "check_rate_limit", "get_redis"]

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis | None:
    return _redis


async def init_cache() -> None:
    global _redis
    try:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
        )
        await _redis.ping()
        FastAPICache.init(RedisBackend(_redis), prefix="pb")  # pb = physics-blog
        logger.info("Redis cache connected: %s", settings.REDIS_URL)
    except Exception as exc:
        logger.warning("Redis unavailable at startup (%s) — running without cache", exc)
        _redis = None


async def close_cache() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        logger.info("Redis connection closed")


# ── Key invalidation ──────────────────────────────────────────────────────────

async def _delete_pattern(pattern: str) -> int:
    if not _redis:
        return 0
    deleted = 0
    try:
        async for key in _redis.scan_iter(match=pattern):
            await _redis.delete(key)
            deleted += 1
    except Exception as exc:
        logger.warning("Cache invalidation failed for pattern %s: %s", pattern, exc)
    return deleted


async def invalidate_post(slug: str) -> None:
    await _delete_pattern(f"pb:*get_post*{slug}*")


async def invalidate_lists() -> None:
    await _delete_pattern("pb:*list_posts*")
    await _delete_pattern("pb:*list_all_posts*")


async def invalidate_taxonomy() -> None:
    await _delete_pattern("pb:*list_categories*")
    await _delete_pattern("pb:*list_tags*")


async def invalidate_comments(slug: str) -> None:
    await _delete_pattern(f"pb:*get_comments*{slug}*")


# ── Rate limiting ─────────────────────────────────────────────────────────────

async def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    Sliding-window counter via Redis INCR.
    Returns True (allow) or False (block).
    Fails open if Redis is unavailable.
    """
    if not _redis:
        return True
    try:
        count = await _redis.incr(key)
        if count == 1:
            await _redis.expire(key, window)
        return count <= limit
    except Exception as exc:
        logger.warning("Rate-limit check failed (%s) — failing open", exc)
        return True