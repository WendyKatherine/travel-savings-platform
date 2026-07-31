from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.entities.transaction import Kind, Transaction
from app.domain.value_objects.money import Money


class TestTransactionCreation:
    """Tests for successful Transaction creation."""

    def test_create_with_valid_data(self):
        """
        Creates a Transaction with valid data.
        Verifies kind defaults to DEPOSIT.
        """
        transaction = Transaction.create(
            id=uuid4(),
            goal_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            amount=Money("100000", "COP"),
            recorded_at=datetime.now(UTC),
            recorded_by="user-example",
        )

        assert transaction.kind == Kind.DEPOSIT


class TestTransactionInvariants:
    """Tests for domain invariants (validation at creation)."""

    @pytest.mark.parametrize(
        "non_positive_amount",
        [
            Money("0", "COP"),
            Money("-1", "COP"),
        ],
    )
    def test_creation_for_invariants_amount_positive(self, non_positive_amount):
        """
        Raises ValueError when amount is zero or negative.
        """
        with pytest.raises(ValueError, match=r"The 'amount' field must be a positive number"):
            Transaction.create(
                id=uuid4(),
                goal_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
                amount=non_positive_amount,
                recorded_at=datetime.now(UTC),
                recorded_by="user-example",
            )


class TestTransactionFrozen:
    """Verifies Transaction is truly immutable (frozen dataclass)."""

    def test_cannot_modify_fields_after_creation(self):
        """
        Attempting to reassign any field raises AttributeError
        (guaranteed by frozen=True on the dataclass).
        """
        txn = Transaction.create(
            id=uuid4(),
            goal_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            amount=Money("50000", "COP"),
            recorded_at=datetime.now(UTC),
            recorded_by="editor-42",
        )

        with pytest.raises(AttributeError):
            txn.amount = Money("99999", "COP")
