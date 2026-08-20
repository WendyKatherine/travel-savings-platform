"""
test_record_deposit.py — Tests for the RecordDepositUseCase.

The use case is exercised against the in-memory fakes of both
persistence ports, so no database is involved. This proves the
dependency-inversion point: the use case depends on the contracts
(the ports), not on the concrete storage implementations.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.use_cases.record_deposit import RecordDepositUseCase
from app.domain.entities.transaction import Kind
from app.domain.entities.travel_goal import Status, TravelGoal, TravelGoalError
from app.domain.value_objects.money import Money
from tests.fakes.in_memory_transaction_repository import InMemoryTransactionRepository
from tests.fakes.in_memory_travel_goal_repository import InMemoryTravelGoalRepository


@pytest.fixture
def goal_repo() -> InMemoryTravelGoalRepository:
    """In-memory fake for goals, fresh per test."""
    return InMemoryTravelGoalRepository()


@pytest.fixture
def transaction_repo() -> InMemoryTransactionRepository:
    """In-memory fake for ledger entries, fresh per test."""
    return InMemoryTransactionRepository()


@pytest.fixture
def use_case(goal_repo, transaction_repo) -> RecordDepositUseCase:
    """Use case wired to both fakes via the ports."""
    return RecordDepositUseCase(goal_port=goal_repo, transaction_port=transaction_repo)


def _make_goal(status: Status = Status.ACTIVE) -> TravelGoal:
    """Helper: a goal with a COP target (ACTIVE by default)."""
    return TravelGoal(
        id=uuid4(),
        owner_id="user-123",
        destination="Cartagena",
        target=Money("1500000", "COP"),
        created_at=datetime.now(UTC),
        status=status,
    )


class TestRecordDeposit:
    """Tests for RecordDepositUseCase against the in-memory fakes."""

    async def test_persists_ledger_entry_on_valid_deposit(
        self, use_case, goal_repo, transaction_repo
    ):
        """
        A valid deposit is saved through the transaction port.
        """
        goal = _make_goal()
        await goal_repo.save(goal)

        result = await use_case.execute(
            goal_id=goal.id,
            idempotency_key=uuid4(),
            amount=Money("50000", "COP"),
            recorded_by="editor-42",
        )

        assert result is not None
        assert result.kind == Kind.DEPOSIT
        assert result.goal_id == goal.id
        assert result.amount == Money("50000", "COP")
        assert transaction_repo.saved == [result]

    async def test_returns_none_when_goal_not_found(self, use_case, transaction_repo):
        """
        A missing goal returns None and nothing is persisted.
        """
        result = await use_case.execute(
            goal_id=uuid4(),
            idempotency_key=uuid4(),
            amount=Money("50000", "COP"),
            recorded_by="editor-42",
        )

        assert result is None
        assert transaction_repo.saved == []

    async def test_propagates_error_on_non_active_goal(self, use_case, goal_repo, transaction_repo):
        """
        A deposit on a CLOSED goal propagates TravelGoalError.
        """
        goal = _make_goal(status=Status.CLOSED)
        await goal_repo.save(goal)

        with pytest.raises(TravelGoalError, match="non-active"):
            await use_case.execute(
                goal_id=goal.id,
                idempotency_key=uuid4(),
                amount=Money("50000", "COP"),
                recorded_by="editor-42",
            )

        assert transaction_repo.saved == []

    async def test_propagates_error_on_currency_mismatch(
        self, use_case, goal_repo, transaction_repo
    ):
        """
        A deposit in a different currency propagates TravelGoalError.
        """
        goal = _make_goal()
        await goal_repo.save(goal)

        with pytest.raises(TravelGoalError, match="currency"):
            await use_case.execute(
                goal_id=goal.id,
                idempotency_key=uuid4(),
                amount=Money("100", "USD"),
                recorded_by="editor-42",
            )

        assert transaction_repo.saved == []

    async def test_forwards_idempotency_key_to_the_repository(
        self, use_case, goal_repo, transaction_repo
    ):
        """
        The key received by the use case reaches the repository's store.
        """
        goal = _make_goal()
        await goal_repo.save(goal)
        key = uuid4()

        result = await use_case.execute(
            goal_id=goal.id,
            idempotency_key=key,
            amount=Money("50000", "COP"),
            recorded_by="editor-42",
        )

        assert await transaction_repo.get_by_idempotency_key(key) == result
