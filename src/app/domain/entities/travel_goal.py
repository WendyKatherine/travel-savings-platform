"""
travel_goal.py - TravelGoal domain entity (aggregate root)

Represents a user's savings goal toward a travel package.
Each goal has an owner, a destination, a target amount (Money),
and a lifecycle status. The saved balance is calculated, not stored.

In Clean Architecture, TravelGoal is a domain entity:
self-validating, identity-driven (UUID), and money-aware.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from app.domain.value_objects.money import Money


class Status(Enum):
    ACTIVE = "ACTIVE"


@dataclass
class TravelGoal:
    """
    Aggregate root: a user's savings goal toward a travel destination.

    Attributes:
        id:          Unique identity (UUID). Generated at the boundary.
        owner_id:    Reference to the affiliated user.
        destination: Travel destination or package name (e.g. "Cartagena").
        target:      Target amount as a Money value object.
        status:      Lifecycle status — starts as ACTIVE.
        created_at:  Timestamp of creation (UTC, timezone-aware). Generated at the boundary.

    Invariants:
        - destination must not be empty.
        - target must be positive.
        - status starts as ACTIVE.

    Usage::

        from uuid import uuid4
        from datetime import datetime, timezone

        goal = TravelGoal.create(
            id=uuid4(),
            owner_id="user-123",
            destination="Cartagena",
            target=Money("1500000", "COP"),
            created_at=datetime.now(timezone.utc),
        )
        print(goal.status)  # Status.ACTIVE
    """
    id: UUID
    owner_id: str
    destination: str
    target: Money
    created_at: datetime
    status: Status = field(default=Status.ACTIVE)

    def __post_init__(self):
        if not self.destination or not self.destination.strip():
            raise ValueError("The 'destination' field cannot be empty.") from None

        zero = Money("0", self.target.currency)
        if self.target <= zero:
            raise ValueError("The 'target' field must be a positive number") from None

    @classmethod
    def create(
        cls,
        id: UUID,
        owner_id: str,
        destination: str,
        target: Money,
        created_at: datetime
    ) -> "TravelGoal":
        """
        Factory method. id and created_at are generated at the boundary
        and passed in, keeping the entity deterministic and testable.
        """
        return cls(
            id=id,
            owner_id=owner_id,
            destination=destination,
            target=target,
            status=Status.ACTIVE,
            created_at=created_at,
        )
