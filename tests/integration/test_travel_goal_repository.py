"""
test_travel_goal_repository.py - Integration tests for PostgresTravelGoalRepository.

These tests exercise the persistence port against a REAL Postgres
(spun up by testcontainers in conftest.py). No HTTP endpoint is
involved: the repository is called directly, just like the use case
calls the port. The endpoint belongs to the interface layer and gets
its own tests later.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.entities.travel_goal import TravelGoal
from app.domain.value_objects.money import Money
from app.infrastructure.persistence.travel_goal_repository import PostgresTravelGoalRepository


@pytest.mark.integration
async def test_round_trip_preserves_goal_by_value(session):
    """save() then get_by_id() returns the same goal, rebuilt from the DB."""
    goal = TravelGoal.create(
        id=uuid4(),
        owner_id="user-123",
        destination="Cartagena",
        target=Money("1500000", "COP"),
        created_at=datetime.now(UTC),
    )

    repo = PostgresTravelGoalRepository(session)
    await repo.save(goal)
    await session.commit()  # the repo joins transactions, it does not close them

    loaded = await repo.get_by_id(goal.id)

    assert loaded == goal
    assert loaded is not goal  # Postgres rebuilt a new object; equality is by value


@pytest.mark.integration
async def test_get_by_id_returns_none_for_unknown_id(session):
    """The port contract: an id that does not exist yields None."""
    repo = PostgresTravelGoalRepository(session)
    loaded = await repo.get_by_id(uuid4())
    assert loaded is None
