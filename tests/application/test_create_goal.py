"""
test_create_goal.py — Tests for the CreateGoalUseCase.

The use case is exercised against the in-memory fake of the persistence
port, so no database is involved. This proves the dependency-inversion
point: the use case depends on the contract (the port), not on the
concrete storage implementation.
"""

from datetime import datetime
from uuid import UUID

import pytest

from app.application.use_cases.create_goal import CreateGoalUseCase
from app.domain.entities.travel_goal import Status, TravelGoal
from app.domain.value_objects.money import Money
from tests.fakes.in_memory_travel_goal_repository import InMemoryTravelGoalRepository


@pytest.fixture
def repository():
    """In-memory fake, fresh for every test."""
    return InMemoryTravelGoalRepository()


@pytest.fixture
def use_case(repository):
    """Use case wired to the fake via the port — dependency inversion in action."""
    return CreateGoalUseCase(goal_port=repository)


OWNER_ID = "user-123"
DESTINATION = "Cartagena"
TARGET = Money("1500000", "COP")


class TestCreateGoal:
    """Tests for CreateGoalUseCase against the in-memory fake repository."""

    async def test_creates_active_goal_with_generated_identity(self, use_case):
        """
        execute() returns a TravelGoal with ACTIVE status, a generated
        identity and the exact data that was submitted.
        """
        result = await use_case.execute(
            owner_id=OWNER_ID,
            destination=DESTINATION,
            target=TARGET,
        )

        assert isinstance(result, TravelGoal)
        assert result.status == Status.ACTIVE
        assert result.owner_id == OWNER_ID
        assert result.destination == DESTINATION
        assert result.target == TARGET
        assert isinstance(result.id, UUID)
        assert isinstance(result.created_at, datetime)

    async def test_persists_goal_after_execute(self, use_case, repository):
        """
        The created goal is actually persisted: after execute(),
        get_by_id() returns the same object the use case saved.
        """
        result = await use_case.execute(
            owner_id=OWNER_ID,
            destination=DESTINATION,
            target=TARGET,
        )

        stored = await repository.get_by_id(result.id)
        assert stored == result

    async def test_raises_value_error_on_empty_destination(self, use_case):
        """
        Domain invariants are not swallowed: an empty destination
        makes the entity raise ValueError, and the use case lets it
        propagate to the caller.
        """
        with pytest.raises(ValueError, match="destination"):
            await use_case.execute(owner_id=OWNER_ID, destination="", target=TARGET)
