"""
conftest.py - Fixtures for integration tests against a real Postgres.

Integration tests do NOT use the DATABASE_URL from .env: that URL points
to the development database (docker-compose). Each test run spins up its
own ephemeral Postgres via testcontainers (random port), runs the Alembic
migrations against it, and tears it down at the end. Isolated and
reproducible - the dev DB is never touched.
"""

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.infrastructure.config.settings import get_settings


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """Start an ephemeral Postgres, migrate it, and yield its async URL."""
    original_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:16-alpine") as postgres:
        url = postgres.get_connection_url(driver="asyncpg")

        # migrations/env.py overrides the Alembic URL from settings, so
        # point settings at the container and clear the cache first.
        os.environ["DATABASE_URL"] = url
        get_settings.cache_clear()
        try:
            command.upgrade(Config("alembic.ini"), "head")
            yield url
        finally:
            if original_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = original_url
            get_settings.cache_clear()


@pytest.fixture
async def session(database_url: str) -> AsyncIterator[AsyncSession]:
    """Async session isolated per test.

    Each test runs inside its own transaction: session commits become
    savepoint releases (join_transaction_mode="create_savepoint"), and the
    outer transaction is rolled back at teardown - so data committed by one
    test never leaks into the next one.
    """
    engine = create_async_engine(database_url)
    connection = await engine.connect()
    transaction = await connection.begin()
    async_session = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        async with async_session() as s:
            yield s
    finally:
        await transaction.rollback()
        await connection.close()
        await engine.dispose()
