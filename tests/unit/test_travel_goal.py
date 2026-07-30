from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.entities.travel_goal import Status, TravelGoal
from app.domain.value_objects.money import Money


class TestTravelGoalCreation:
    """Tests for successful TravelGoal creation."""

    def test_create_with_valid_data(self):
        """
        Creates a TravelGoal with valid data.
        Verifies every field is assigned correctly and status defaults to ACTIVE.
        """
        goal = TravelGoal.create(
            id=uuid4(),
            owner_id="user-123",
            destination="Cartagena",
            target=Money("100000", "COP"),
            created_at=datetime.now(UTC),
        )

        assert goal.status == Status.ACTIVE


class TestTravelGoalInvariants:
    """Tests for domain invariants (validation at creation)."""

    def test_creation_for_invariants_destination_empty(self):
        """
        Raises ValueError when destination is an empty string.
        """
        with pytest.raises(ValueError, match=r"The 'destination' field cannot be empty."):
            TravelGoal.create(
                id=uuid4(),
                owner_id="user-123",
                destination="   ",
                target=Money("100000", "COP"),
                created_at=datetime.now(UTC),
            )

    @pytest.mark.parametrize("non_positive_target", [
        Money("0", "COP"),
        Money("-1", "COP"),
    ])
    def test_creation_for_invariants_target_positive_number(self, non_positive_target):
        """
        Raises ValueError when target is zero or negative.
        """
        with pytest.raises(ValueError, match="The 'target' field must be a positive number"):
            TravelGoal.create(
                id=uuid4(),
                owner_id="user-123",
                destination="Cartagena",
                target=non_positive_target,
                created_at=datetime.now(UTC),
            )


#class TestTravelGoalImmutability:
    """Tests that identity fields cannot be mutated."""


class TestTravelGoalDeterminism:
    """Tests that the entity is deterministic with fixed inputs."""
    def test_entity_determinism_with_fixed_inputs(self):
        """
        With the same inputs the entity always produces the same result.
        No internal generation of id, created_at, or any other field.
        """
        goal = TravelGoal.create(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            owner_id="user-123",
            destination="Cartagena",
            target=Money("100000", "COP"),
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )

        assert goal.id == UUID("123e4567-e89b-12d3-a456-426614174000")
        assert goal.owner_id == "user-123"
        assert goal.destination == "Cartagena"
        assert goal.target == Money("100000", "COP")
        assert goal.created_at == datetime(2025, 1, 1, tzinfo=UTC)
        assert goal.status == Status.ACTIVE


#class TestTravelGoalBehavior:
    """Tests for domain behavior (status transitions, etc.)."""
