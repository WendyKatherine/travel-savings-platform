"""FastAPI dependency wiring lives in the interface layer.

Keeping DI here (not in infrastructure) means adapters stay unaware of the
web framework, and use cases receive their ports assembled from one place.
"""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.persistence.database import get_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_redis() -> Redis:
    return redis_client
