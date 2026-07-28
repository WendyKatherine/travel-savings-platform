"""Async Redis client (OTP store, idempotency fast-path, rate limiting)."""

from redis.asyncio import Redis

from app.infrastructure.config.settings import get_settings


def build_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


redis_client: Redis = build_redis()
