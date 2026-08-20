"""
test_transactions_api.py — Integration tests for POST /goals/{goal_id}/deposits.

Proves the pipeline is wired correctly (session dependency -> Postgres
repositories -> RecordDepositUseCase -> real Postgres), NOT the business
rules: those are covered by the domain and application tests.

Same wiring as test_goals_api.py: the endpoint still asks for
get_db_session, but app.dependency_overrides replaces it with the conftest
session (bound to an ephemeral testcontainers Postgres). The conftest runs
Alembic migrations against that database, so this file also exercises the
transactions migrations (table + FK + UNIQUE idempotency_key).

The Idempotency-Key header is required by the endpoint, so every request
sends one; TestIdempotency exercises the durable idempotency guarantee
against the real UNIQUE constraint (the part the in-memory fake cannot
simulate).
"""

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.transaction import TransactionModel
from app.interface.api.app import create_app
from app.interface.api.dependencies import get_db_session

pytestmark = pytest.mark.integration


def make_goal_payload(**overrides: str) -> dict[str, str]:
    """Build a valid POST /goals body (same shape as test_goals_api)."""
    payload = {
        "owner_id": "user-123",
        "destination": "Cartagena",
        "target_amount": "1500000",
        "currency": "COP",
    }
    payload.update(overrides)
    return payload


def make_deposit_payload(**overrides: str) -> dict[str, str]:
    """Build a valid deposit body, overriding any field per test."""
    payload = {
        "amount": "50000",
        "currency": "COP",
        "recorded_by": "editor-42",
    }
    payload.update(overrides)
    return payload


def deposit_headers(key: str | None = None) -> dict[str, str]:
    """Headers for a deposit request; a fresh key when none is given."""
    return {"Idempotency-Key": key or str(uuid4())}


async def post_deposit(
    client: AsyncClient,
    goal_id: str,
    *,
    headers: dict[str, str] | None = None,
    **overrides: str,
) -> Response:
    """POST a deposit against a goal, sending a valid Idempotency-Key."""
    return await client.post(
        f"/goals/{goal_id}/deposits",
        json=make_deposit_payload(**overrides),
        headers=headers or deposit_headers(),
    )


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    App under test with the session dependency overridden.

    Replicates the production Unit of Work boundary: commit after success,
    rollback + re-raise on error. The conftest teardown rolls back the
    outer transaction, so no data leaks between tests.
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


class TestRecordDepositApi:
    """POST /goals/{goal_id}/deposits through the HTTP layer — status codes and payloads."""

    async def test_records_deposit_returns_201_with_public_payload(
        self, client: AsyncClient
    ) -> None:
        """A valid deposit returns 201 and the public DepositResponse shape."""
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        response = await post_deposit(client, goal_id)

        assert response.status_code == 201
        data = response.json()
        assert UUID(data["id"])  # raises ValueError if the id is not a valid UUID
        assert data["goal_id"] == goal_id
        assert data["amount"] == "COP 50,000.00"
        assert data["kind"] == "DEPOSIT"
        assert data["recorded_by"] == "editor-42"

    async def test_deposit_is_persisted_with_fk_after_201(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """Bonus: the 201 really committed — a ledger row with the FK exists."""
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        response = await post_deposit(client, goal_id)
        txn_id = response.json()["id"]

        result = await session.execute(
            select(TransactionModel).where(TransactionModel.id == UUID(txn_id))
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
        assert stored.goal_id == UUID(goal_id)
        assert stored.amount_value == Decimal("50000.00")
        assert stored.amount_currency == "COP"
        assert stored.kind == "DEPOSIT"

    async def test_returns_404_when_goal_does_not_exist(self, client: AsyncClient) -> None:
        """A valid UUID with no matching goal returns 404, never 500."""
        goal_id = uuid4()

        response = await post_deposit(client, str(goal_id))

        assert response.status_code == 404
        assert response.json()["detail"] == f"Goal {goal_id} not found"

    async def test_returns_400_when_currency_does_not_match_goal(self, client: AsyncClient) -> None:
        """A deposit in a different currency is a domain rejection: 400."""
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        response = await post_deposit(client, goal_id, currency="USD")

        assert response.status_code == 400
        assert "currency" in response.json()["detail"]

    async def test_returns_400_when_amount_is_not_positive(self, client: AsyncClient) -> None:
        """A non-positive amount is a domain rejection: 400, never 500."""
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        response = await post_deposit(client, goal_id, amount="0")

        assert response.status_code == 400
        assert "positive" in response.json()["detail"]

    async def test_returns_422_when_body_is_malformed(self, client: AsyncClient) -> None:
        """A body missing required fields is rejected by FastAPI with 422."""
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        response = await client.post(
            f"/goals/{goal_id}/deposits",
            json={"amount": "50000"},
            headers=deposit_headers(),
        )

        assert response.status_code == 422

    async def test_nothing_is_persisted_after_400(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """Bonus: the rollback worked — a failed deposit leaves no ledger rows."""
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        await post_deposit(client, goal_id, currency="USD")

        result = await session.execute(select(func.count()).select_from(TransactionModel))
        assert result.scalar_one() == 0


class TestIdempotency:
    """Durable idempotency against the real UNIQUE constraint (the jewel)."""

    async def test_same_key_twice_creates_one_entry(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """
        The idempotency proof: two requests with the same key, one entry.

        A network retry must never duplicate money: the second request
        collides with the UNIQUE constraint, the use case replays the
        stored entry, and both responses carry the same transaction id.
        """
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]
        key = str(uuid4())

        first = await post_deposit(client, goal_id, headers=deposit_headers(key))
        second = await post_deposit(client, goal_id, headers=deposit_headers(key))

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]

        result = await session.execute(select(func.count()).select_from(TransactionModel))
        assert result.scalar_one() == 1

    async def test_different_keys_create_two_entries(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """
        Different keys are different intentions: both deposits are stored.

        The same amount with two different keys must produce two ledger
        entries — the idempotency key scopes "same request", not "same
        amount".
        """
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        first = await post_deposit(client, goal_id)
        second = await post_deposit(client, goal_id)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] != second.json()["id"]

        result = await session.execute(select(func.count()).select_from(TransactionModel))
        assert result.scalar_one() == 2

    async def test_returns_422_without_idempotency_key(self, client: AsyncClient) -> None:
        """
        A missing Idempotency-Key header is rejected with 422.

        The header is required (a money endpoint without idempotency
        protection should not exist); FastAPI validates it before the
        endpoint runs.
        """
        created = await client.post("/goals", json=make_goal_payload())
        goal_id = created.json()["id"]

        response = await client.post(f"/goals/{goal_id}/deposits", json=make_deposit_payload())

        assert response.status_code == 422
