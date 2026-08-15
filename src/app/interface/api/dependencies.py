"""FastAPI dependency wiring lives in the interface layer.

Keeping DI here (not in infrastructure) means adapters stay unaware of the
web framework, and use cases receive their ports assembled from one place.
"""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.persistence.database import SessionFactory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an AsyncSession and own the transaction boundary (Unit of Work).

    The repository participates in the transaction but never commits:
    this dependency confirms it (commit) after the endpoint succeeds,
    rolls back and re-raises on any error, and always closes the session
    via the SessionFactory context manager.
    """
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


async def get_redis() -> Redis:
    """Return the shared async Redis client."""
    return redis_client
