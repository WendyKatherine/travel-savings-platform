from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.entities.transaction import Transaction
from app.domain.entities.travel_goal import Status, TravelGoal
from app.domain.value_objects.money import Money, MoneyError


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


class TestTravelGoalImmutability:
    """Tests that identity fields cannot be mutated."""

    def _make_goal(self) -> TravelGoal:
        """Helper: a goal with a COP target."""
        return TravelGoal.create(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            owner_id="user-123",
            destination="Cartagena",
            target=Money("1500000", "COP"),
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
        )

    def test_id_cannot_be_reassigned(self):
        """
        Reassigning id after creation raises AttributeError.
        """
        goal = self._make_goal()

        with pytest.raises(AttributeError, match="id is immutable"):
            goal.id = uuid4()

    def test_created_at_cannot_be_reassigned(self):
        """
        Reassigning created_at after creation raises AttributeError.
        """
        goal = self._make_goal()

        with pytest.raises(AttributeError, match="created_at is immutable"):
            goal.created_at = datetime.now(UTC)

    def test_owner_id_cannot_be_reassigned(self):
        """
        Reassigning owner_id after creation raises AttributeError.
        """
        goal = self._make_goal()

        with pytest.raises(AttributeError, match="owner_id is immutable"):
            goal.owner_id = "another-user"

    def test_other_fields_remain_mutable(self):
        """
        Non-identity fields (e.g. destination) can still be updated.
        """
        goal = self._make_goal()

        goal.destination = "Santa Marta"

        assert goal.destination == "Santa Marta"


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


class TestTravelGoalBalance:
    """Tests for the balance calculation from ledger transactions."""

    def _make_goal(self) -> TravelGoal:
        """Helper: a goal with a COP target."""
        return TravelGoal.create(
            id=uuid4(),
            owner_id="user-123",
            destination="Cartagena",
            target=Money("1500000", "COP"),
            created_at=datetime.now(UTC),
        )

    def _make_transaction(self, amount: Money) -> Transaction:
        """Helper: a DEPOSIT transaction for the goal's ledger."""
        return Transaction.create(
            id=uuid4(),
            goal_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            amount=amount,
            recorded_at=datetime.now(UTC),
            recorded_by="editor-42",
        )

    def test_balance_with_no_transactions_is_zero(self):
        """
        A goal with an empty ledger has balance zero in its own currency.
        """
        goal = self._make_goal()

        assert goal.balance([]) == Money("0", "COP")

    def test_balance_with_single_deposit(self):
        """
        A single DEPOSIT makes the balance equal to that amount.
        """
        goal = self._make_goal()

        balance = goal.balance([self._make_transaction(Money("50000", "COP"))])

        assert balance == Money("50000", "COP")

    def test_balance_with_multiple_deposits_sums_them(self):
        """
        Multiple DEPOSITs accumulate into the total balance.
        """
        goal = self._make_goal()
        transactions = [
            self._make_transaction(Money("50000", "COP")),
            self._make_transaction(Money("25000", "COP")),
            self._make_transaction(Money("1000", "COP")),
        ]

        balance = goal.balance(transactions)

        assert balance == Money("76000", "COP")

    def test_balance_raises_when_transaction_currency_mismatch(self):
        """
        A transaction in a different currency breaks the Money addition guard.
        """
        goal = self._make_goal()
        foreign = self._make_transaction(Money("100", "USD"))

        with pytest.raises(MoneyError, match="Cannot add"):
            goal.balance([foreign])

    def test_balance_is_pure_no_mutation(self):
        """
        Calling balance does not mutate the goal or the input list.
        """
        goal = self._make_goal()
        transactions = [
            self._make_transaction(Money("50000", "COP")),
            self._make_transaction(Money("25000", "COP")),
        ]
        goal_before = goal
        txns_before = list(transactions)

        goal.balance(transactions)

        assert goal == goal_before
        assert transactions == txns_before