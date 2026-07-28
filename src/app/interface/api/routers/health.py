"""Health endpoints.

Liveness (/healthz) answers "is the process up?" with no dependencies.
Readiness (/readyz) answers "can we actually serve traffic?" by probing
Postgres and Redis. Orchestrators use them differently, so they are split.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.interface.api.dependencies import get_db_session, get_redis

router = APIRouter(tags=["health"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]


@router.get("/healthz")
async def liveness() -> dict[str, Literal["ok"]]:
    return {"status": "ok"}


@router.get("/readyz")
async def readiness(session: SessionDep, redis: RedisDep) -> dict[str, str]:
    checks: dict[str, str] = {}

    try:
        await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        # Readiness must report status, never raise.
        checks["postgres"] = "unavailable"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    ready = checks["postgres"] == "ok" and checks["redis"] == "ok"
    checks["status"] = "ready" if ready else "degraded"
    return checks
