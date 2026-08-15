"""
test_goals_api.py — Integration tests for POST /goals through the HTTP layer.

Proves the pipeline is wired correctly (session dependency -> Postgres
repository -> use case -> real Postgres), NOT the business rules: those
are covered by the domain and application tests.

The endpoint still asks for get_db_session, but app.dependency_overrides
replaces it with the conftest session (bound to an ephemeral testcontainers
Postgres). The override replicates the production Unit of Work pattern, so
the flow under test is identical to production — including commit/rollback.
"""

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.travel_goal import TravelGoalModel
from app.interface.api.app import create_app
from app.interface.api.dependencies import get_db_session

pytestmark = pytest.mark.integration


def make_payload(**overrides: str) -> dict[str, str]:
    """Build a valid POST /goals body, overriding any field per test."""
    payload = {
        "owner_id": "user-123",
        "destination": "Cartagena",
        "target_amount": "1500000",
        "currency": "COP",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    App under test with the session dependency overridden.

    Reuses the conftest ``session`` fixture (ephemeral Postgres, one
    transaction per test with savepoints) and replicates the production
    Unit of Work boundary: commit after success, rollback + re-raise on
    error. The conftest teardown rolls back the outer transaction, so no
    data leaks between tests.
    """
    app = create_app()

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestCreateGoalApi:
    """POST /goals through the HTTP layer — status codes and payloads."""

    async def test_creates_goal_returns_201_with_public_payload(self, client: AsyncClient) -> None:
        """A valid body returns 201 and the public GoalResponse shape."""
        response = await client.post("/goals", json=make_payload())

        assert response.status_code == 201
        data = response.json()
        assert UUID(data["id"])  # raises ValueError if the id is not a valid UUID
        assert data["destination"] == "Cartagena"
        assert data["target"] == "COP 1,500,000.00"
        assert data["status"] == "ACTIVE"

    async def test_returns_400_when_destination_is_empty(self, client: AsyncClient) -> None:
        """Empty destination is a client error: 400, never 500."""
        response = await client.post("/goals", json=make_payload(destination=""))

        assert response.status_code == 400
        assert response.json()["detail"] == "The 'destination' field cannot be empty."

    async def test_returns_400_when_currency_is_unsupported(self, client: AsyncClient) -> None:
        """Unsupported currency is a client error: 400, never 500."""
        response = await client.post("/goals", json=make_payload(currency="XYZ"))

        assert response.status_code == 400
        assert "Unsupported currency" in response.json()["detail"]

    async def test_goal_is_persisted_after_201(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """Bonus: the 201 really committed — the row exists in the database."""
        response = await client.post("/goals", json=make_payload())

        result = await session.execute(
            select(TravelGoalModel).where(TravelGoalModel.id == UUID(response.json()["id"]))
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.destination == "Cartagena"
        assert stored.target_amount == Decimal("1500000.00")
        assert stored.target_currency == "COP"

    async def test_nothing_is_persisted_after_400(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """Bonus: the rollback worked — a failed request leaves no rows."""
        await client.post("/goals", json=make_payload(currency="XYZ"))

        result = await session.execute(select(func.count()).select_from(TravelGoalModel))
        assert result.scalar_one() == 0
