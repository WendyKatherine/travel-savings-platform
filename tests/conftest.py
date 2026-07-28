"""Test configuration.

Required settings are injected before the app is imported, so unit tests
run without a real database or Redis. Integration tests (added later) will
spin up a real Postgres via testcontainers instead of these defaults.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
