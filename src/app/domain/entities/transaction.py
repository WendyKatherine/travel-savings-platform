"""
transaction.py — Transaction domain entity (append-only ledger entry)

Represents an immutable movement against a savings goal.
Each line in the ledger is frozen after creation — never edited, never deleted.
Amount is always positive; the direction (deposit, etc.) is carried by kind,
not by the sign of the amount. This makes auditing simpler.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from app.domain.exceptions import DomainError
from app.domain.value_objects.money import Money


class TransactionError(DomainError):
    """Raised when a Transaction invariant is violated."""


class Kind(Enum):
    """Direction of a ledger movement."""

    DEPOSIT = "DEPOSIT"


@dataclass(frozen=True)
class Transaction:
    """
    Immutable ledger entry for a savings goal.

    Attributes:
        id:           Unique identity (UUID).
        goal_id:      Reference to the target TravelGoal (by id).
        amount:       Positive Money amount. Direction comes from kind.
        recorded_at:  Timestamp of registration (UTC, timezone-aware).
        recorded_by:  Editor id who registered the movement (audit trail).
        kind:         Movement type — starts as DEPOSIT.

    Invariants:
        - amount must be positive (validated at creation).
        - The object is frozen: no field can change after construction.

    Usage::

        from uuid import uuid4
        from datetime import datetime, timezone

        txn = Transaction(
            id=uuid4(),
            goal_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            amount=Money("50000", "COP"),
            recorded_at=datetime.now(timezone.utc),
            recorded_by="editor-42",
            kind=Kind.DEPOSIT,
        )
    """

    id: UUID
    goal_id: UUID
    amount: Money
    recorded_at: datetime
    recorded_by: str
    kind: Kind = field(default=Kind.DEPOSIT)

    def __post_init__(self) -> None:
        zero = Money("0", self.amount.currency)
        if self.amount <= zero:
            raise TransactionError("The 'amount' field must be a positive number") from None

    @classmethod
    def create(
        cls,
        id: UUID,
        goal_id: UUID,
        amount: Money,
        recorded_at: datetime,
        recorded_by: str,
    ) -> "Transaction":
        """
        Factory method. kind defaults to DEPOSIT; amount is validated
        as positive in ``__post_init__``.
        """
        return cls(
            id=id,
            goal_id=goal_id,
            amount=amount,
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            kind=Kind.DEPOSIT,
        )
